import pandas as pd
from collections import Counter, defaultdict
from .estatisticas import (
    LISTA_PRIMOS, LISTA_FIBONACCI, LISTA_MULTIPLOS_3, 
    NUM_DEZENAS_SORTEADAS, analisar_ciclos, analisar_atraso_relativo,
    criar_faixas_estatisticas
)

# --- FUNÇÕES AUXILIARES ---
def calcular_matriz_transicao(lista_estados):
    transicoes = defaultdict(list)
    for i in range(len(lista_estados) - 1):
        transicoes[lista_estados[i]].append(lista_estados[i+1])
    probabilidades = {}
    for estado, proximos in transicoes.items():
        total = len(proximos)
        probabilidades[estado] = {k: round(v/total * 100, 1) for k, v in Counter(proximos).items()}
    return probabilidades

def calc_soma(b): return sum(b)
def calc_deltas(b): 
    sb = sorted(b)
    return sum([sb[i+1]-sb[i] for i in range(len(sb)-1)])

def calc_temp_n(bolas, df, idx, janela):
    if idx < janela: return 0
    historico = df.iloc[idx-janela : idx][[f'Bola{i}' for i in range(1, 7)]].values.flatten()
    historico = [x for x in historico if pd.notna(x)]
    c = Counter(historico)
    return sum(c[b] for b in bolas)

# Wrappers para as chamadas de Temp
def calc_temp_39(b, df, idx): return calc_temp_n(b, df, idx, 39)
def calc_temp_21(b, df, idx): return calc_temp_n(b, df, idx, 21)

def gerar_mapa_calor_recente(df, janela):
    cols = [f'Bola{i}' for i in range(1, 7)]
    recorte = df.tail(janela)[cols].values.flatten()
    return dict(Counter([int(x) for x in recorte if pd.notna(x)]))

# --- ANÁLISES ---

def analisar_tendencia_generica(df, nome, func_valor):
    cols = [f'Bola{i}' for i in range(1, 7)]
    hist = [str(func_valor(row[cols].dropna().astype(int).tolist())) for _, row in df.iterrows()]
    matriz = calcular_matriz_transicao(hist)
    ultimo = hist[-1] if hist else "N/A"
    return {'indicador': nome, 'ultimo_estado': ultimo, 'probabilidades': matriz.get(ultimo, {})}

def analisar_tendencia_faixas(df, nome, func_valor):
    cols = [f'Bola{i}' for i in range(1, 7)]
    valores = []
    for _, row in df.iterrows():
        bolas = row[cols].dropna().astype(int).tolist()
        try: val = func_valor(bolas, df, row.name)
        except TypeError: val = func_valor(bolas)
        valores.append(val)
    
    if not valores: return {}
    s = pd.Series(valores)
    mu, sigma = s.mean(), s.std()
    
    def classificar(v):
        if v < mu - 1.5*sigma: return "Muito Baixo"
        if v < mu - 0.5*sigma: return "Baixo"
        if v <= mu + 0.5*sigma: return "Média"
        if v <= mu + 1.5*sigma: return "Alto"
        return "Muito Alto"

    estados = [classificar(v) for v in valores]
    matriz = calcular_matriz_transicao(estados)
    ultimo = estados[-1] if estados else "N/A"
    return {'indicador': nome, 'ultimo_estado': ultimo, 'probabilidades': matriz.get(ultimo, {}), 'limites': (mu, sigma)}

def analisar_tendencia_repetidas(df):
    """Analisa quantas repetiram do concurso IMEDIATAMENTE anterior"""
    cols = [f'Bola{i}' for i in range(1, 7)]
    jogos = [set(row[cols].dropna().astype(int).tolist()) for _, row in df.iterrows()]
    hist = []
    for i in range(1, len(jogos)):
        rep = len(jogos[i].intersection(jogos[i-1]))
        hist.append(str(rep))
    
    if not hist: return {'ultimo_estado': '0', 'probabilidades': {}}
    matriz = calcular_matriz_transicao(hist)
    ultimo = hist[-1]
    return {'indicador': 'Repetidas', 'ultimo_estado': ultimo, 'probabilidades': matriz.get(ultimo, {})}

def analisar_tendencia_padrao(df, tipo):
    # ... (Mesma lógica do anterior para Quadrantes, Linhas, etc.) ...
    cols = [f'Bola{i}' for i in range(1, 7)]
    hist = []
    for _, row in df.iterrows():
        bolas = row[cols].dropna().astype(int).tolist()
        if tipo == 'linhas': hist.append(str(len(set([(d-1)//10 for d in bolas]))))
        elif tipo == 'colunas': hist.append(str(len(set([(d-1)%10 for d in bolas]))))
        elif tipo == 'sequenciais':
            sb = sorted(bolas)
            max_s = 1; curr = 1
            for i in range(len(sb)-1):
                if sb[i+1] == sb[i]+1: curr+=1
                else: max_s=max(max_s, curr); curr=1
            hist.append(str(max(max_s, curr) if max(max_s, curr)>1 else 0))
        elif tipo == 'quadrantes':
            q=[0,0,0,0]
            for d in bolas:
                if d in [1,2,3,4,5,11,12,13,14,15,21,22,23,24,25]: q[0]+=1
                elif d in [6,7,8,9,10,16,17,18,19,20,26,27,28,29,30]: q[1]+=1
                elif d in [31,32,33,34,35,41,42,43,44,45,51,52,53,54,55]: q[2]+=1
                else: q[3]+=1
            hist.append(f"{q[0]}-{q[1]}-{q[2]}-{q[3]}")
            
    matriz = calcular_matriz_transicao(hist)
    ultimo = hist[-1] if hist else "N/A"
    return {'indicador': tipo.title(), 'ultimo_estado': ultimo, 'probabilidades': matriz.get(ultimo, {})}

# ... (Manter analisar_tendencia_concentracao e max_repeticao iguais) ...
def analisar_tendencia_concentracao(df, tipo='iniciais'):
    cols = [f'Bola{i}' for i in range(1, 7)]
    hist = []
    for _, row in df.iterrows():
        bolas = row[cols].dropna().astype(int).tolist()
        d = [str(x).zfill(2)[0] if tipo=='iniciais' else str(x).zfill(2)[-1] for x in bolas]
        hist.append(str(max(Counter(d).values())))
    matriz = calcular_matriz_transicao(hist)
    ultimo = hist[-1] if hist else "0"
    return {'indicador': f'Conc {tipo}', 'ultimo_estado': ultimo, 'probabilidades': matriz.get(ultimo, {})}

def analisar_tendencia_max_repeticao(df, janela):
    cols = [f'Bola{i}' for i in range(1, 7)]
    todos = df[cols].values.tolist()
    hist = []
    for i in range(janela, len(todos)):
        atual = [int(x) for x in todos[i] if pd.notna(x)]
        recorte = [int(n) for sub in todos[i-janela:i] for n in sub if pd.notna(n)]
        c = Counter(recorte)
        freqs = [c[n] for n in atual]
        hist.append(str(max(freqs)) if freqs else "0")
    
    if not hist: return {'ultimo_estado': '0', 'probabilidades': {}}
    matriz = calcular_matriz_transicao(hist)
    ultimo = hist[-1]
    return {'indicador': f'MaxRep {janela}', 'ultimo_estado': ultimo, 'probabilidades': matriz.get(ultimo, {})}

# --- MESTRA ---
def gerar_perfil_preditivo_completo(df):
    # Helpers
    def c_primos(b): return len([x for x in b if x in LISTA_PRIMOS])
    def c_pares(b): return len([x for x in b if x % 2 == 0])
    def c_fibo(b): return len([x for x in b if x in LISTA_FIBONACCI])
    def c_mult3(b): return len([x for x in b if x in LISTA_MULTIPLOS_3])
    
    p = {}
    # Grupo 1
    p['soma'] = analisar_tendencia_faixas(df, 'Soma', calc_soma)
    p['deltas'] = analisar_tendencia_faixas(df, 'Deltas', calc_deltas)
    p['primos'] = analisar_tendencia_generica(df, 'Primos', c_primos)
    p['pares'] = analisar_tendencia_generica(df, 'Pares', c_pares)
    p['fibo'] = analisar_tendencia_generica(df, 'Fibo', c_fibo)
    p['mult3'] = analisar_tendencia_generica(df, 'Mult3', c_mult3)
    
    # Grupo 2
    p['sequenciais'] = analisar_tendencia_padrao(df, 'sequenciais')
    p['linhas'] = analisar_tendencia_padrao(df, 'linhas')
    p['colunas'] = analisar_tendencia_padrao(df, 'colunas')
    p['quadrantes'] = analisar_tendencia_padrao(df, 'quadrantes')
    
    # Grupo 3 (Novos)
    p['temp39'] = analisar_tendencia_faixas(df, 'Temp39', calc_temp_39)
    p['temp21'] = analisar_tendencia_faixas(df, 'Temp21', calc_temp_21) # <--- NOVO
    p['repetidas'] = analisar_tendencia_repetidas(df) # <--- NOVO
    p['iniciais'] = analisar_tendencia_concentracao(df, 'iniciais')
    p['finais'] = analisar_tendencia_concentracao(df, 'finais')
    p['max_rep_39'] = analisar_tendencia_max_repeticao(df, 39)
    p['max_rep_21'] = analisar_tendencia_max_repeticao(df, 21)
    
    # Mapas
    p['mapa_39'] = gerar_mapa_calor_recente(df, 39)
    p['mapa_21'] = gerar_mapa_calor_recente(df, 21)
    
    # Pressão
    cic = analisar_ciclos(df)
    p['ciclo_faltantes'] = set(cic['faltam_sair']) if cic else set()
    
    # Atrasos com Z-Score > 3 (Parametrizável aqui ou na visualização)
    atr = analisar_atraso_relativo(df)
    # Filtra aqui para o SCORE (só pontua se for critico > 2.0, por exemplo)
    p['atrasadas_criticas'] = set(d['dezena'] for d in atr if d['z_score'] > 2.0)
    # Passa a lista completa ordenada para a visualização decidir o corte
    p['lista_atrasos_completa'] = atr 
    
    cols = [f'Bola{i}' for i in range(1, 7)]
    p['ultimo_sorteio'] = set(df.iloc[-1][cols].dropna().astype(int).tolist())
    
    return p

def extrair_perfil_alvo_completo(predicao, top_n_quadrantes=12):
    alvo = {}
    keys = ['soma', 'primos', 'pares', 'fibo', 'mult3', 'deltas', 
            'iniciais', 'finais', 'sequenciais', 'linhas', 'colunas', 
            'quadrantes', 'temp39', 'temp21', 'repetidas', # Novos
            'max_rep_39', 'max_rep_21']
            
    for k in keys:
        if k not in predicao: continue
        probs = predicao[k]['probabilidades']
        
        # Lógica para Quadrantes: Trazer mais opções (Top N)
        limit = top_n_quadrantes if k == 'quadrantes' else 2
        
        top = sorted(probs, key=probs.get, reverse=True)[:limit]
        
        try:
            if k not in ['quadrantes', 'soma', 'deltas', 'temp39', 'temp21']:
                alvo[k] = [int(x) for x in top]
            else:
                alvo[k] = top
        except:
            alvo[k] = top
            
    return alvo