# app/util/config_mega.py

# Constantes da Mega-Sena
UNIVERSO_DEZENAS = 60
NUM_DEZENAS_SORTEADAS = 6
DATABASE_NAME = 'megasena_db.sqlite3'
TABLE_NAME = 'resultados_megasena' # Certifique-se que sua tabela tem esse nome

# Listas Especiais para Mega-Sena (1-60)
LISTA_PRIMOS = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59]
LISTA_FIBONACCI = [1, 2, 3, 5, 8, 13, 21, 34, 55]
LISTA_MULTIPLOS_3 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57, 60]

# Moldura da Mega-Sena (Volante 6x10)
# Linha 1 inteira, Linha 6 inteira, Coluna 1 e Coluna 10 (excluindo cantos já contados)
DEZENAS_MOLDURA = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10,      # Linha 1
    11, 21, 31, 41, 51,                 # Coluna 1 (meio)
    20, 30, 40, 50,                     # Coluna 10 (meio)
    52, 53, 54, 55, 56, 57, 58, 59, 60  # Linha 6 (excluindo 51 e 60 que já estariam nas colunas se não cuidado, mas aqui simplificado)
]
# Garante valores únicos e ordenados
DEZENAS_MOLDURA = sorted(list(set(DEZENAS_MOLDURA)))