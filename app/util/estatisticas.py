# app/util/estatisticas.py
import pandas as pd
import numpy as np
from collections import Counter
import sqlite3
# Importação absoluta correta
from app.util.config_mega import TABLE_NAME, LISTA_PRIMOS, LISTA_FIBONACCI, LISTA_MULTIPLOS_3, NUM_DEZENAS_SORTEADAS

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def carregar_todos_resultados(db_path):
    conn = get_db_connection(db_path)
    cols = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    query = f"SELECT Concurso, Data, {', '.join(cols)} FROM {TABLE_NAME} ORDER BY Concurso ASC"
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Erro DB: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# --- Funções Auxiliares ---

def calcular_distribuicao_qtd(df, func_contagem):
    total = len(df)
    contador = Counter()
    for _, row in df.iterrows():
        bolas = row[[f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]].dropna().astype(int).tolist()
        qtd = func_contagem(bolas)
        contador[qtd] += 1
    return [{'qtd': k, 'contagem': v, 'percentual': round((v/total*100), 1)} for k, v in sorted(contador.items())]

def criar_faixas_estatisticas(lista_valores):
    """
    Divide uma lista de valores em 5 faixas baseadas na Média e Desvio Padrão.
    Faixa 3 (Meio) = Media +/- 0.5 * Desvio
    """
    if not lista_valores: return []
    
    s = pd.Series(lista_valores)
    media = s.mean()
    desvio = s.std()
    total = len(s)

    # Definição dos limites (Limiares)
    limite_muito_baixo = media - (1.5 * desvio)
    limite_baixo      = media - (0.5 * desvio)
    limite_alto       = media + (0.5 * desvio)
    limite_muito_alto = media + (1.5 * desvio)

    # Contagem
    faixas = {
        "Muito Baixo": 0,
        "Baixo": 0,
        "Média": 0,
        "Alto": 0,
        "Muito Alto": 0
    }
    
    # Definição das labels para exibição (ex: "120 - 150")
    labels_faixa = {
        "Muito Baixo": f"< {int(limite_muito_baixo)}",
        "Baixo":       f"{int(limite_muito_baixo)} a {int(limite_baixo)}",
        "Média":       f"{int(limite_baixo)} a {int(limite_alto)}",
        "Alto":        f"{int(limite_alto)} a {int(limite_muito_alto)}",
        "Muito Alto":  f"> {int(limite_muito_alto)}"
    }

    for v in lista_valores:
        if v < limite_muito_baixo: faixas["Muito Baixo"] += 1
        elif v < limite_baixo:     faixas["Baixo"] += 1
        elif v <= limite_alto:     faixas["Média"] += 1 # Faixa Central
        elif v <= limite_muito_alto: faixas["Alto"] += 1
        else:                      faixas["Muito Alto"] += 1

    # Formatação final
    resultado = []
    ordem = ["Muito Baixo", "Baixo", "Média", "Alto", "Muito Alto"]
    
    for nome in ordem:
        qtd = faixas[nome]
        resultado.append({
            'nome_faixa': nome,
            'intervalo': labels_faixa[nome],
            'contagem': qtd,
            'percentual': round((qtd / total * 100), 1)
        })
    return resultado

# --- Análises ---

def analisar_basicos(df):
    def conta_primos(bolas): return len([x for x in bolas if x in LISTA_PRIMOS])
    def conta_fibo(bolas): return len([x for x in bolas if x in LISTA_FIBONACCI])
    def conta_mult3(bolas): return len([x for x in bolas if x in LISTA_MULTIPLOS_3])

    return {
        'primos': calcular_distribuicao_qtd(df, conta_primos),
        'fibo': calcular_distribuicao_qtd(df, conta_fibo),
        'mult3': calcular_distribuicao_qtd(df, conta_mult3)
    }

def analisar_iniciais_finais(df):
    total = len(df)
    stats_ini = Counter()
    stats_fim = Counter()
    for _, row in df.iterrows():
        bolas = row[[f'Bola{i}' for i in range(1, 7)]].dropna().astype(int).tolist()
        iniciais = [str(d).zfill(2)[0] for d in bolas]
        stats_ini[max(Counter(iniciais).values())] += 1
        finais = [str(d).zfill(2)[-1] for d in bolas]
        stats_fim[max(Counter(finais).values())] += 1
        
    def fmt(c): return [{'qtd': k, 'contagem': v, 'percentual': round(v/total*100, 1)} for k,v in sorted(c.items())]
    return fmt(stats_ini), fmt(stats_fim)

def analisar_sequenciais(df):
    total = len(df)
    stats_seq = Counter()
    for _, row in df.iterrows():
        bolas = sorted(row[[f'Bola{i}' for i in range(1, 7)]].dropna().astype(int).tolist())
        max_seq = 1; atual_seq = 1
        for i in range(len(bolas)-1):
            if bolas[i+1] == bolas[i]+1: atual_seq += 1
            else:
                max_seq = max(max_seq, atual_seq); atual_seq = 1
        max_seq = max(max_seq, atual_seq)
        stats_seq[max_seq if max_seq > 1 else 0] += 1
    return [{'qtd': k, 'contagem': v, 'percentual': round(v/total*100, 1)} for k,v in sorted(stats_seq.items())]

def analisar_repetidas_anterior(df):
    total = len(df) - 1; stats = Counter()
    if total < 1: return []
    jogos = [set(row[[f'Bola{i}' for i in range(1, 7)]].dropna().astype(int).tolist()) for _, row in df.iterrows()]
    for i in range(1, len(jogos)):
        stats[len(jogos[i].intersection(jogos[i-1]))] += 1
    return [{'qtd': k, 'contagem': v, 'percentual': round(v/total*100, 1)} for k,v in sorted(stats.items())]

# --- NOVAS LÓGICAS DE 5 FAIXAS ---

def analisar_somas_distribuicao(df):
    """Calcula a distribuição das Somas em 5 faixas dinâmicas"""
    somas = []
    for _, row in df.iterrows():
        bolas = row[[f'Bola{i}' for i in range(1, 7)]].dropna().astype(int).tolist()
        somas.append(sum(bolas))
    
    return criar_faixas_estatisticas(somas)

def analisar_frequencia_periodo_distribuicao(df, janela):
    """
    Calcula a 'Soma de Frequência' (Temperatura) e distribui em 5 faixas dinâmicas.
    Confirmação da lógica: Contagem de todas as dezenas nos X jogos anteriores.
    """
    cols_bolas = [f'Bola{i}' for i in range(1, 7)]
    todos_jogos = df[cols_bolas].values.tolist()
    
    lista_metricas = []
    
    # Começa a partir da 'janela', pois os primeiros jogos não têm histórico suficiente
    for i in range(janela, len(todos_jogos)):
        jogo_atual = [int(x) for x in todos_jogos[i] if pd.notna(x)]
        
        # Pega o recorte histórico (os 'janela' jogos anteriores)
        historico = todos_jogos[i-janela : i]
        
        # Achatamos a lista para contar a frequência de cada número nesse período
        flat_historico = [int(num) for sublist in historico for num in sublist if pd.notna(num)]
        contagem_hist = Counter(flat_historico)
        
        # Somamos a popularidade das dezenas do jogo atual
        soma_frequencia = sum(contagem_hist[num] for num in jogo_atual)
        lista_metricas.append(soma_frequencia)

    return criar_faixas_estatisticas(lista_metricas)

# --- Funções Antigas (Ainda usadas no index para tabelas simples) ---

def analisar_frequencia_geral(df):
    total = len(df)
    if total == 0: return [], [], []
    cols = [f'Bola{i}' for i in range(1, 7)]
    todas = [int(x) for col in cols for x in df[col].dropna()]
    c = Counter(todas)
    res = [{'dezena': k, 'contagem': v, 'percentual': round(v/total*100, 2)} for k,v in c.items()]
    return sorted(res, key=lambda x:x['dezena']), sorted(res, key=lambda x:x['contagem'], reverse=True)[:10], sorted(res, key=lambda x:x['contagem'])[:10]

def analisar_pares_impares(df):
    total = len(df); stats = Counter()
    for _, row in df.iterrows():
        bolas = row[[f'Bola{i}' for i in range(1, 7)]].dropna().astype(int).tolist()
        pares = len([x for x in bolas if x%2==0])
        stats[(pares, 6-pares)] += 1
    return [{'pares': p, 'impares': i, 'contagem': c, 'percentual': round(c/total*100, 2)} for (p,i),c in sorted(stats.items())]

# app/util/estatisticas.py

# app/util/estatisticas.py

def analisar_distribuicao_maximas(df, janela):
    """
    Calcula a Máxima Repetição de cada jogo e agrupa nas faixas solicitadas.
    Range 39: 6, 7, 8, 9, >=10
    Range 21: 4, 5, 6, 7, >=8
    """
    if df.empty or len(df) < janela: return []

    # 1. Configuração das Faixas baseada na janela
    if janela == 39:
        # Faixas: 6, 7, 8, 9, >=10
        faixas = {6: 0, 7: 0, 8: 0, 9: 0, 10: 0} 
        labels = {6: "6", 7: "7", 8: "8", 9: "9", 10: ">= 10"}
        limite_min = 6
        limite_max = 10
    elif janela == 21:
        # Faixas: 4, 5, 6, 7, >=8
        faixas = {4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
        labels = {4: "4", 5: "5", 6: "6", 7: "7", 8: ">= 8"}
        limite_min = 4
        limite_max = 8
    else:
        return []

    # 2. Processamento dos dados (igual anteriormente)
    cols_bolas = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    todos_jogos = []
    for _, row in df.iterrows():
        try: todos_jogos.append(row[cols_bolas].dropna().astype(int).tolist())
        except: continue

    total_analisado = 0
    
    for i in range(janela, len(todos_jogos)):
        jogo_atual = todos_jogos[i]
        historico = todos_jogos[i-janela : i]
        
        # Achata histórico e conta
        flat_historico = [num for sublist in historico for num in sublist]
        contagem_hist = Counter(flat_historico)
        
        # Pega a MÁXIMA repetição encontrada neste jogo
        freqs_atuais = [contagem_hist[num] for num in jogo_atual]
        if not freqs_atuais: continue
            
        max_rep = max(freqs_atuais)
        total_analisado += 1

        # 3. Categorização nas Faixas
        if max_rep < limite_min:
            # Se for menor que o mínimo (ex: 3), ignora ou conta como 'Outros'
            # Aqui vamos focar nas faixas pedidas, então não incrementa faixas
            pass
        elif max_rep >= limite_max:
            faixas[limite_max] += 1 # Conta no balde "Maior ou Igual"
        else:
            if max_rep in faixas:
                faixas[max_rep] += 1

    # 4. Formatação do Resultado
    resultado = []
    for k, label in labels.items():
        qtd = faixas[k]
        resultado.append({
            'faixa': label,
            'contagem': qtd,
            'percentual': round(qtd / total_analisado * 100, 1) if total_analisado > 0 else 0
        })
        
    return resultado

def analisar_distribuicao_quadrantes(df):
    """
    Analisa o perfil de quadrantes de cada sorteio.
    Q1 (Sup. Esq), Q2 (Sup. Dir), Q3 (Inf. Esq), Q4 (Inf. Dir)
    """
    total_sorteios = len(df)
    if total_sorteios == 0: return []
    
    q1 = {1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 21, 22, 23, 24, 25}
    q2 = {6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 26, 27, 28, 29, 30}
    q3 = {31, 32, 33, 34, 35, 41, 42, 43, 44, 45, 51, 52, 53, 54, 55}
    q4 = {36, 37, 38, 39, 40, 46, 47, 48, 49, 50, 56, 57, 58, 59, 60}

    cols_bolas = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    stats_perfis = Counter()

    for _, row in df.iterrows():
        bolas = row[cols_bolas].dropna().astype(int).tolist()
        
        c1 = len([x for x in bolas if x in q1])
        c2 = len([x for x in bolas if x in q2])
        c3 = len([x for x in bolas if x in q3])
        c4 = len([x for x in bolas if x in q4])
        
        # Cria o perfil ex: "2-1-2-1"
        perfil = f"{c1}-{c2}-{c3}-{c4}"
        stats_perfis[perfil] += 1

    resultado = []
    # Ordena pelos perfis que mais saíram
    for perfil, contagem in sorted(stats_perfis.items(), key=lambda x: x[1], reverse=True):
        resultado.append({
            'perfil': perfil,
            'contagem': contagem,
            'percentual': round(contagem / total_sorteios * 100, 2)
        })
        
    return resultado

def analisar_ciclos(df):
    """
    Analisa o Ciclo Atual:
    - Quantos sorteios já ocorreram neste ciclo.
    - Quais dezenas faltam sair para fechar o ciclo.
    """
    if df.empty: return None

    cols_bolas = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    todos_jogos = df[cols_bolas].values.tolist()

    # Conjunto de todas as dezenas possíveis (1 a 60)
    universo = set(range(1, 61))
    
    # Dezenas que já saíram no ciclo atual
    dezenas_saiu_ciclo = set()
    concursos_no_ciclo = 0
    
    # Percorre do ÚLTIMO jogo para trás até fechar o ciclo
    # Mas a lógica de ciclo é progressiva. Vamos simular do inicio.
    
    ciclo_id = 1
    dezenas_neste_ciclo = set()
    inicio_ciclo_index = 0

    # Vamos percorrer a história para achar o estado ATUAL
    for i, jogo in enumerate(todos_jogos):
        nums = {int(x) for x in jogo if pd.notna(x)}
        
        # Se o ciclo estava completo, inicia um novo
        if len(dezenas_neste_ciclo) == 60:
            dezenas_neste_ciclo = set()
            ciclo_id += 1
            inicio_ciclo_index = i
            
        dezenas_neste_ciclo.update(nums)

    # O estado atual é o que sobrou no 'dezenas_neste_ciclo'
    faltam_sair = list(universo - dezenas_neste_ciclo)
    faltam_sair.sort()
    
    sorteios_neste_ciclo = len(todos_jogos) - inicio_ciclo_index

    return {
        'id_ciclo': ciclo_id,
        'qtd_jogos': sorteios_neste_ciclo,
        'faltam_sair': faltam_sair,
        'qtd_faltam': len(faltam_sair),
        'progresso': round(len(dezenas_neste_ciclo) / 60 * 100, 1)
    }

def analisar_padrao_linhas_colunas(df):
    """
    Analisa a distribuição geométrica (Grid 6x10).
    Retorna os padrões mais comuns de preenchimento.
    Ex Linhas: 2-1-1-1-1-0 (significa 2 dezenas numa linha, 1 em outras 4, 0 na ultima)
    """
    stats_linhas = Counter()
    stats_colunas = Counter()
    total = len(df)

    cols_bolas = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]

    for _, row in df.iterrows():
        bolas = row[cols_bolas].dropna().astype(int).tolist()
        
        # Mega Sena: Linhas 0-5, Colunas 0-9 (Baseado na dezena - 1)
        # Ex: 60 -> (59)//10 = 5 (Linha 6), (59)%10 = 9 (Coluna 10)
        linhas_counts = [0]*6
        colunas_counts = [0]*10
        
        for b in bolas:
            idx = b - 1
            l = idx // 10
            c = idx % 10
            if 0 <= l < 6: linhas_counts[l] += 1
            if 0 <= c < 10: colunas_counts[c] += 1
            
        # Gera a assinatura (ordenada para agrupar padrões iguais, ex: 2-1-1 é igual a 1-2-1 em estrutura)
        # Mas aqui queremos a estrutura de quantidade, ex: "5 linhas ocupadas"
        
        # Padrão de Ocupação (quantas linhas tiveram dezenas?)
        qtd_linhas_ocupadas = 6 - linhas_counts.count(0)
        qtd_colunas_ocupadas = 10 - colunas_counts.count(0)
        
        stats_linhas[qtd_linhas_ocupadas] += 1
        stats_colunas[qtd_colunas_ocupadas] += 1

    def formatar(c):
        return [{'qtd': k, 'contagem': v, 'percentual': round(v/total*100, 1)} for k,v in sorted(c.items())]

    return {
        'linhas_ocupadas': formatar(stats_linhas),
        'colunas_ocupadas': formatar(stats_colunas)
    }

def analisar_atrasos(df):
    """
    Calcula o Atraso Atual de cada uma das 60 dezenas.
    Isso é CRUCIAL para o sistema de pontuação preditiva.
    """
    cols_bolas = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    todos_jogos = df[cols_bolas].values.tolist()
    total_jogos = len(todos_jogos)
    
    # Dicionário {Dezena: Ultimo_Concurso_Visto}
    ultima_aparicao = {i: -1 for i in range(1, 61)}
    
    # Percorre cronologicamente
    for idx, jogo in enumerate(todos_jogos):
        nums = [int(x) for x in jogo if pd.notna(x)]
        for n in nums:
            ultima_aparicao[n] = idx # Salva o índice do jogo (0 a N)
            
    # Calcula atraso
    resultado = []
    for dezena in range(1, 61):
        ultimo_idx = ultima_aparicao[dezena]
        if ultimo_idx == -1:
            atraso = total_jogos # Nunca saiu (improvavel na mega, mas possivel em amostragem pequena)
        else:
            atraso = (total_jogos - 1) - ultimo_idx
            
        resultado.append({
            'dezena': dezena,
            'atraso': atraso
        })
        
    # Ordena pelos mais atrasados primeiro
    resultado.sort(key=lambda x: x['atraso'], reverse=True)
    
    return resultado

def analisar_deltas(df):
    """
    Analisa a soma das diferenças (Deltas).
    Mede se o jogo é muito 'espalhado' ou 'agrupado'.
    """
    cols_bolas = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    somas_deltas = []
    
    for _, row in df.iterrows():
        bolas = sorted(row[cols_bolas].dropna().astype(int).tolist())
        # Calcula diferenças: (B2-B1) + (B3-B2) ...
        # Matematicamente, Soma Deltas = (Bn - B1)
        # Mas vamos fazer a soma de cada salto para visualização
        deltas = [bolas[i+1] - bolas[i] for i in range(len(bolas)-1)]
        soma_deltas = sum(deltas)
        somas_deltas.append(soma_deltas)
        
    # Usa a nossa função de faixas criada anteriormente
    return criar_faixas_estatisticas(somas_deltas)

def analisar_atraso_relativo(df, limite_desvio=3.0):
    """
    Calcula o Z-Score do atraso atual.
    Z-Score = (Atraso Atual - Média Histórica) / Desvio Padrão Histórico.
    Se Z-Score > 3, significa que é um evento estatístico raríssimo (Anomalia).
    """
    cols = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    todos_jogos = df[cols].values.tolist()
    total_jogos = len(todos_jogos)
    
    intervalos = {k: [] for k in range(1, 61)}
    ultima_aparicao = {k: -1 for k in range(1, 61)}
    
    for idx, jogo in enumerate(todos_jogos):
        nums = [int(x) for x in jogo if pd.notna(x)]
        for n in nums:
            if ultima_aparicao[n] != -1:
                gap = idx - ultima_aparicao[n] - 1
                intervalos[n].append(gap)
            ultima_aparicao[n] = idx
            
    resultado = []
    for dezena in range(1, 61):
        atraso_atual = (total_jogos - 1) - ultima_aparicao[dezena]
        gaps = intervalos[dezena]
        
        if len(gaps) > 1:
            media = np.mean(gaps)
            desvio = np.std(gaps)
            
            # Evita divisão por zero se desvio for 0
            if desvio > 0:
                z_score = (atraso_atual - media) / desvio
            else:
                z_score = 0
        else:
            media = 0
            z_score = 0
            
        # Filtra pelo parametro (Default > 3 sigmas)
        # Se quiser flexibilidade, retornamos tudo e filtramos na ponta
        if z_score > 0: # Retorna todos que estão acima da média para ordenação
            resultado.append({
                'dezena': dezena,
                'atraso': atraso_atual,
                'media': round(media, 1),
                'z_score': round(z_score, 2)
            })
            
    # Ordena pelos mais críticos (Z-Score maior)
    resultado.sort(key=lambda x: x['z_score'], reverse=True)
    return resultado