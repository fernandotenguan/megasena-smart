# -*- coding: utf-8 -*-
"""
Este script realiza a coleta e armazenamento de resultados de loterias da Caixa
(Lotofácil e Mega-Sena) de forma incremental, consolidando a lógica em uma
classe base para evitar duplicação de código.
"""
import logging
import os
import sqlite3
import time
from typing import Optional

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- Configurações Globais ---
os.environ['WDM_LOG'] = '0'
DIRETORIO_SCRIPT = os.path.dirname(os.path.abspath(__file__))
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

class BaseLotteryScraper:
    """
    Classe base abstrata para coletar resultados de loterias da Caixa.
    Contém toda a lógica comum de setup, navegação e persistência de dados.
    """

    def __init__(self, lottery_name: str, url: str, db_name: str, table_name: str, num_balls: int, ball_list_xpath: str):
        """
        Inicializa o scraper com as configurações específicas da loteria.
        """
        self.lottery_name = lottery_name
        self.url_pagina = url
        self.nome_banco_dados = db_name
        self.caminho_banco_dados = os.path.join(DIRETORIO_SCRIPT, self.nome_banco_dados)
        self.nome_tabela_resultados = table_name
        self.num_balls = num_balls
        # --- NOVO: XPath específico para as dezenas ---
        self.ball_list_xpath = ball_list_xpath

        self.driver: Optional[WebDriver] = None
        self._setup_logging()

    def _setup_logging(self):
        """Configura o sistema de logging para o script."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.getLogger("selenium").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    def _setup_driver(self) -> Optional[WebDriver]:
        """Configura e inicializa o WebDriver do Selenium em modo headless."""
        options = webdriver.ChromeOptions()
        prefs = {
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument(f"user-agent={USER_AGENT}")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--log-level=3')

        try:
            logging.info("Iniciando o ChromeDriver via webdriver-manager...")
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            logging.info("ChromeDriver iniciado com sucesso.")
            return driver
        except Exception as e:
            logging.error(f"Falha ao iniciar o ChromeDriver: {e}")
            logging.error("Verifique sua conexão com a internet ou a configuração do ChromeDriver.")
            return None

    def initialize_database(self):
        """Cria o banco de dados e a tabela de resultados se não existirem."""
        logging.info(f"Verificando/Inicializando o banco de dados para {self.lottery_name}...")
        colunas_bolas_sql = ", ".join([f"Bola{i} INTEGER" for i in range(1, self.num_balls + 1)])
        query_create_table = f"""
        CREATE TABLE IF NOT EXISTS {self.nome_tabela_resultados} (
            Concurso INTEGER PRIMARY KEY,
            Data TEXT,
            {colunas_bolas_sql}
        );"""

        try:
            with sqlite3.connect(self.caminho_banco_dados) as conn:
                cursor = conn.cursor()
                cursor.execute(query_create_table)
                conn.commit()
            logging.info("Banco de dados e tabela verificados com sucesso.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao inicializar o banco de dados: {e}")
            raise

    def _get_latest_contest_from_db(self) -> int:
        """Busca o número do último concurso salvo no banco de dados."""
        if not os.path.exists(self.caminho_banco_dados):
            return 0
        try:
            with sqlite3.connect(self.caminho_banco_dados) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT MAX(Concurso) FROM {self.nome_tabela_resultados}")
                resultado = cursor.fetchone()
                return resultado[0] if resultado and resultado[0] is not None else 0
        except sqlite3.Error as e:
            logging.error(f"Erro ao consultar último concurso no banco de dados: {e}")
            return 0

    def _save_results_to_db(self, df_results: pd.DataFrame) -> bool:
        """Salva um DataFrame de resultados no banco de dados."""
        if df_results.empty:
            logging.info("Nenhum novo resultado para salvar.")
            return True
        try:
            with sqlite3.connect(self.caminho_banco_dados) as conn:
                df_results.to_sql(
                    self.nome_tabela_resultados, conn, if_exists="append", index=False
                )
            logging.info(f"Salvo com sucesso: {len(df_results)} novo(s) resultado(s) para {self.lottery_name}.")
            return True
        except sqlite3.IntegrityError:
            logging.warning("Erro de integridade: Tentativa de inserir concursos duplicados. Ignorando.")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado ao salvar dados no banco: {e}")
            return False

    def _search_contest(self, contest_number: int) -> bool:
        """Preenche o campo de busca e pesquisa por um concurso específico."""
        try:
            input_concurso = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "buscaConcurso"))
            )
            input_concurso.clear()
            input_concurso.send_keys(str(contest_number))
            input_concurso.send_keys(u'\ue007')  # Envia a tecla Enter
            return True
        except TimeoutException:
            logging.error("Não foi possível encontrar o campo de busca de concurso na página.")
            return False

    def _scrape_contest_data(self, contest_number: int) -> Optional[pd.DataFrame]:
        """Extrai os dados de um concurso da página após a busca."""
        try:
            WebDriverWait(self.driver, 15).until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, '//span[contains(text(), "Concurso ")]'),
                    f"Concurso {contest_number} "
                )
            )
            header_text = self.driver.find_element(By.XPATH, '//span[contains(text(), "Concurso ")]').text
            date_str = header_text.split('(')[-1].split(')')[0].strip() if '(' in header_text else None

            # --- CORRIGIDO: Usa o XPath específico da loteria ---
            dezena_elements = self.driver.find_elements(By.XPATH, self.ball_list_xpath)
            dezenas = [int(e.text) for e in dezena_elements if e.text.isdigit()]

            if len(dezenas) != self.num_balls:
                logging.warning(f"Concurso {contest_number} encontrado, mas com {len(dezenas)}/{self.num_balls} dezenas. Pulando.")
                return None

            data = {
                'Concurso': contest_number,
                'Data': date_str,
                **{f'Bola{i+1}': dezenas[i] for i in range(self.num_balls)}
            }
            return pd.DataFrame([data])
        except TimeoutException:
            logging.info(f"O concurso {contest_number} não foi encontrado na página. Fim da coleta para {self.lottery_name}.")
            return None
        except (NoSuchElementException, IndexError, ValueError) as e:
            logging.error(f"Erro ao extrair dados para o concurso {contest_number}: {e}")
            return None

    def run_incremental_scrape(self):
        """Executa a coleta incremental a partir do último concurso salvo."""
        logging.info(f"--- Iniciando coleta incremental da {self.lottery_name} ---")
        self.initialize_database()

        self.driver = self._setup_driver()
        if not self.driver:
            logging.critical("WebDriver não pôde ser iniciado. Abortando a execução.")
            return

        try:
            latest_contest_db = self._get_latest_contest_from_db()
            logging.info(f"Último concurso no banco de dados: {latest_contest_db}")

            self.driver.get(self.url_pagina)
            try:
                cookie_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
                cookie_button.click()
                logging.info("Botão de cookies aceito.")
            except TimeoutException:
                logging.info("Nenhum pop-up de cookies encontrado ou já foi aceito.")

            next_contest = latest_contest_db + 1

            while True:
                logging.info(f"Buscando concurso {next_contest}...")
                if not self._search_contest(next_contest):
                    break

                df_new_result = self._scrape_contest_data(next_contest)
                if df_new_result is None:
                    break

                if self._save_results_to_db(df_new_result):
                    logging.info(f"Concurso {next_contest} da {self.lottery_name} salvo com sucesso.")
                    next_contest += 1
                else:
                    logging.error("Parando a coleta devido a um erro ao salvar no banco de dados.")
                    break
                
                time.sleep(1)

        except Exception as e:
            logging.critical(f"Um erro inesperado ocorreu durante a coleta da {self.lottery_name}: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
            logging.info(f"--- Coleta incremental da {self.lottery_name} finalizada ---")

# --- Classes Específicas para cada Loteria ---

class LotofacilScraper(BaseLotteryScraper):
    """Scraper para os resultados da Lotofácil."""
    def __init__(self):
        super().__init__(
            lottery_name="Lotofácil",
            url="https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx",
            db_name="lotofacil_db.sqlite3",
            table_name="resultados_lotofacil",
            num_balls=15,
            # XPath específico para a lista de dezenas da Lotofácil
            ball_list_xpath='//ul[contains(@class, "lista-dezenas")]/li'
        )

class MegaSenaScraper(BaseLotteryScraper):
    """Scraper para os resultados da Mega-Sena."""
    def __init__(self):
        super().__init__(
            lottery_name="Mega-Sena",
            url="https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx",
            db_name="megasena_db.sqlite3",
            table_name="resultados_megasena",
            num_balls=6,
            # XPath específico para a lista de dezenas da Mega-Sena
            ball_list_xpath='//ul[contains(@class, "numbers")]/li'
        )

if __name__ == "__main__":
    # --- Execução da Coleta ---
    
    # Coleta de resultados da Lotofácil
    # scraper_loto = LotofacilScraper()
    # scraper_loto.run_incremental_scrape()
    
    # print("\n" + "="*50 + "\n") # Separador visual no log

    # Coleta de resultados da Mega-Sena
    scraper_mega = MegaSenaScraper()
    scraper_mega.run_incremental_scrape()