# app/util/pontuacao.py
from .config_mega import LISTA_PRIMOS, LISTA_MULTIPLOS_3, LISTA_FIBONACCI

def classificar_faixa(valor, limites):
    """
    Classifica um valor numérico em uma das 5 faixas estatísticas (Gauss).
    """
    if not limites or len(limites) != 2:
        return "Indefinido"
        
    mu, sigma = limites
    if valor < mu - 1.5*sigma: return "Muito Baixo"
    if valor < mu - 0.5*sigma: return "Baixo"
    if valor <= mu + 0.5*sigma: return "Média"
    if valor <= mu + 1.5*sigma: return "Alto"
    return "Muito Alto"

def calcular_pontuacao_binaria(jogo, perfil, mapa_39, mapa_21):
    """
    Calcula o Score (0 a 12 pontos) comparando o jogo com o Perfil Alvo.
    """
    score = 0
    dezenas = sorted(jogo)
    
    # --- GRUPO A: Faixas Numéricas (Requer limites mu/sigma) ---
    
    # 1. Soma
    soma = sum(dezenas)
    cat = classificar_faixa(soma, perfil['soma']['limites'])
    if cat in perfil['soma']['alvo']: score += 1
    
    # 2. Deltas
    deltas = sum([dezenas[i+1]-dezenas[i] for i in range(5)])
    cat = classificar_faixa(deltas, perfil['deltas']['limites'])
    if cat in perfil['deltas']['alvo']: score += 1

    # 3. Temp 39
    t39 = sum([mapa_39.get(d, 0) for d in dezenas])
    cat = classificar_faixa(t39, perfil['temp39']['limites'])
    if cat in perfil['temp39']['alvo']: score += 1
    
    # 4. Temp 21
    t21 = sum([mapa_21.get(d, 0) for d in dezenas])
    cat = classificar_faixa(t21, perfil['temp21']['limites'])
    if cat in perfil['temp21']['alvo']: score += 1

    # --- GRUPO B: Contagem Direta (Listas de inteiros) ---
    
    # 5. Pares
    n = len([x for x in dezenas if x % 2 == 0])
    if n in perfil['pares']['alvo']: score += 1
    
    # 6. Primos
    n = len([x for x in dezenas if x in LISTA_PRIMOS])
    if n in perfil['primos']['alvo']: score += 1
    
    # 7. Múltiplos de 3
    n = len([x for x in dezenas if x in LISTA_MULTIPLOS_3])
    if n in perfil['mult3']['alvo']: score += 1
    
    # --- GRUPO C: Categóricos (String vs Int corrigido) ---
    
    # 8. Linhas
    n_linhas = len(set([(d-1)//10 for d in dezenas]))
    # Converte alvo para string para garantir match (ex: 3 vs "3")
    alvos_str = [str(x) for x in perfil['linhas']['alvo']]
    if str(n_linhas) in alvos_str: score += 1
    
    # 9. Colunas
    n_cols = len(set([(d-1)%10 for d in dezenas]))
    alvos_str = [str(x) for x in perfil['colunas']['alvo']]
    if str(n_cols) in alvos_str: score += 1
    
    # 10. Max Repetição 39
    freqs = [mapa_39.get(d, 0) for d in dezenas]
    max_r = str(max(freqs)) if freqs else "0"
    # Correção para lidar com ">=10" ou valores exatos
    match_mr = False
    for alvo in perfil['max_rep_39']['alvo']:
        if ">=" in str(alvo):
            limite = int(str(alvo).replace(">=", "").strip())
            if int(max_r) >= limite: match_mr = True
        elif str(alvo) == max_r:
            match_mr = True
    if match_mr: score += 1
    
    # 11. Max Repetição 21
    freqs = [mapa_21.get(d, 0) for d in dezenas]
    max_r = str(max(freqs)) if freqs else "0"
    match_mr = False
    for alvo in perfil['max_rep_21']['alvo']:
        if ">=" in str(alvo):
            limite = int(str(alvo).replace(">=", "").strip())
            if int(max_r) >= limite: match_mr = True
        elif str(alvo) == max_r:
            match_mr = True
    if match_mr: score += 1

    # --- GRUPO D: Novos Indicadores (Faltava Quadrantes) ---

    # 12. Quadrantes
    # Definição rápida dos conjuntos para performance
    q1_set = {1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 21, 22, 23, 24, 25}
    q2_set = {6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 26, 27, 28, 29, 30}
    q3_set = {31, 32, 33, 34, 35, 41, 42, 43, 44, 45, 51, 52, 53, 54, 55}
    q4_set = {36, 37, 38, 39, 40, 46, 47, 48, 49, 50, 56, 57, 58, 59, 60}

    c1 = len([x for x in dezenas if x in q1_set])
    c2 = len([x for x in dezenas if x in q2_set])
    c3 = len([x for x in dezenas if x in q3_set])
    c4 = len([x for x in dezenas if x in q4_set])
    
    # Formato "2211"
    perfil_atual = f"{c1}{c2}{c3}{c4}"
    
    # Normaliza o alvo removendo traços (ex: "2-2-1-1" vira "2211")
    alvos_quad = [str(x).replace('-', '') for x in perfil['quadrantes']['alvo']]
    
    if perfil_atual in alvos_quad: score += 1
    
    return score