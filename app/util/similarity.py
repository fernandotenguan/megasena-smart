# app/util/similarity.py
import pandas as pd
import numpy as np
# Adicionei LISTA_MULTIPLOS_3 na importação
from .config_mega import NUM_DEZENAS_SORTEADAS, LISTA_PRIMOS, LISTA_MULTIPLOS_3

def classificar_valor_z(valor, media, desvio):
    if desvio == 0: return "Média"
    z = (valor - media) / desvio
    if z < -1.5: return "Muito Baixo"
    if z < -0.5: return "Baixo"
    if z <= 0.5: return "Média"
    if z <= 1.5: return "Alto"
    return "Muito Alto"

def calcular_assinatura_concurso(row, media_soma, std_soma, media_delta, std_delta, media_t39, std_t39, media_t21, std_t21):
    cols = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    dezenas = row[cols].dropna().astype(int).tolist()
    
    # 1. Indicadores EXATOS
    pares = len([d for d in dezenas if d % 2 == 0])
    primos = len([d for d in dezenas if d in LISTA_PRIMOS])       # NOVO
    mult3 = len([d for d in dezenas if d in LISTA_MULTIPLOS_3])   # NOVO
    
    # 2. Soma (FAIXA)
    soma = sum(dezenas)
    faixa_soma = classificar_valor_z(soma, media_soma, std_soma)
    
    # 3. Quadrantes (STRING EXATA)
    q1 = q2 = q3 = q4 = 0
    for d in dezenas:
        col = (d - 1) % 10
        if d <= 30:
            if col < 5: q1 += 1
            else: q2 += 1
        else:
            if col < 5: q3 += 1
            else: q4 += 1
    quadrantes = f"{q1}{q2}{q3}{q4}"
    
    # 4. Soma Deltas (FAIXA)
    dezenas_sort = sorted(dezenas)
    deltas = sum([dezenas_sort[i+1] - dezenas_sort[i] for i in range(len(dezenas)-1)])
    faixa_deltas = classificar_valor_z(deltas, media_delta, std_delta)
    
    # 5. Linhas e Colunas (EXATO QTD)
    linhas = len(set([(d-1)//10 for d in dezenas]))
    colunas = len(set([(d-1)%10 for d in dezenas]))
    
    # 6. Repetidas (EXATO)
    repetidas = int(row.get('Repetidas_Calc', 0))
    
    # 7. Temperaturas (FAIXA)
    temp39 = row.get('Score_Temp39', 0)
    faixa_t39 = classificar_valor_z(temp39, media_t39, std_t39)
    
    temp21 = row.get('Score_Temp21', 0)
    faixa_t21 = classificar_valor_z(temp21, media_t21, std_t21)

    return {
        'concurso': int(row['Concurso']),
        'dezenas': dezenas,
        'soma_real': soma,
        # --- CHECKLIST ---
        'pares': pares,             # Exato
        'primos': primos,           # Exato (NOVO)
        'mult3': mult3,             # Exato (NOVO)
        'faixa_soma': faixa_soma,   # Faixa
        'quadrantes': quadrantes,   # Exato
        'faixa_deltas': faixa_deltas, # Faixa
        'linhas': linhas,           # Exato
        'colunas': colunas,         # Exato
        'repetidas': repetidas,     # Exato
        'faixa_t39': faixa_t39,     # Faixa
        'faixa_t21': faixa_t21      # Faixa
    }

def enriquecer_dataframe_com_metricas(df):
    # (Mantenha o código anterior desta função aqui)
    cols = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    sets_dezenas = df[cols].apply(lambda x: set(x.dropna().astype(int)), axis=1)
    lista_repetidas = [0]
    for i in range(1, len(df)):
        s_atual = sets_dezenas.iloc[i]
        s_ant = sets_dezenas.iloc[i-1]
        lista_repetidas.append(len(s_atual.intersection(s_ant)))
    df['Repetidas_Calc'] = lista_repetidas

    matriz_sorteios = pd.DataFrame(0, index=df.index, columns=range(1, 61))
    for idx, row in df.iterrows():
        dzs = row[cols].dropna().astype(int).tolist()
        matriz_sorteios.loc[idx, dzs] = 1
    
    freq_movel_39 = matriz_sorteios.rolling(window=39, closed='left').sum().fillna(0)
    freq_movel_21 = matriz_sorteios.rolling(window=21, closed='left').sum().fillna(0)
    s39 = (matriz_sorteios * freq_movel_39).sum(axis=1)
    s21 = (matriz_sorteios * freq_movel_21).sum(axis=1)
    df['Score_Temp39'] = s39
    df['Score_Temp21'] = s21
    return df

def buscar_concursos_similares(df_original, concurso_alvo_idx, top_n=20):
    df = df_original.copy()
    df = enriquecer_dataframe_com_metricas(df)
    
    cols_num = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    somas = df[cols_num].sum(axis=1)
    
    deltas_vals = []
    for _, row in df.iterrows():
        d = sorted(row[cols_num].dropna().astype(int).tolist())
        deltas_vals.append(sum([d[i+1]-d[i] for i in range(len(d)-1)]))
        
    medias = {
        'soma': somas.mean(), 'std_soma': somas.std(),
        'delta': np.mean(deltas_vals), 'std_delta': np.std(deltas_vals),
        't39': df['Score_Temp39'].mean(), 'std_t39': df['Score_Temp39'].std(),
        't21': df['Score_Temp21'].mean(), 'std_t21': df['Score_Temp21'].std(),
    }
    
    row_alvo = df.iloc[concurso_alvo_idx]
    ass_alvo = calcular_assinatura_concurso(
        row_alvo, 
        medias['soma'], medias['std_soma'],
        medias['delta'], medias['std_delta'],
        medias['t39'], medias['std_t39'],
        medias['t21'], medias['std_t21']
    )
    
    similares = []
    
    # Loop de busca
    for i in range(50, concurso_alvo_idx):
        row_cand = df.iloc[i]
        ass_cand = calcular_assinatura_concurso(
            row_cand, 
            medias['soma'], medias['std_soma'],
            medias['delta'], medias['std_delta'],
            medias['t39'], medias['std_t39'],
            medias['t21'], medias['std_t21']
        )
        
        matches = []
        
        # 1. Pares
        if ass_alvo['pares'] == ass_cand['pares']: matches.append('Pares')
        # 2. Soma
        if ass_alvo['faixa_soma'] == ass_cand['faixa_soma']: matches.append('Soma')
        # 3. Quadrantes
        if ass_alvo['quadrantes'] == ass_cand['quadrantes']: matches.append('Quadrantes')
        # 4. Repetidas
        if ass_alvo['repetidas'] == ass_cand['repetidas']: matches.append('Repetidas')
        # 5. Deltas
        if ass_alvo['faixa_deltas'] == ass_cand['faixa_deltas']: matches.append('Espalhamento')
        # 6. Linhas
        if ass_alvo['linhas'] == ass_cand['linhas']: matches.append('Linhas')
        # 7. Colunas
        if ass_alvo['colunas'] == ass_cand['colunas']: matches.append('Colunas')
        # 8. Temp 39
        if ass_alvo['faixa_t39'] == ass_cand['faixa_t39']: matches.append('Temp 39')
        # 9. Temp 21
        if ass_alvo['faixa_t21'] == ass_cand['faixa_t21']: matches.append('Temp 21')
        
        # --- NOVOS CRITÉRIOS ---
        # 10. Primos (Exato)
        if ass_alvo['primos'] == ass_cand['primos']: matches.append('Primos')
        # 11. Múltiplos de 3 (Exato)
        if ass_alvo['mult3'] == ass_cand['mult3']: matches.append('Mult 3')
        
        # Cálculo % (Base 11 critérios)
        percentual = (len(matches) / 11) * 100 
        
        if percentual >= 40: # Filtro mínimo visual
            similares.append({
                'concurso': ass_cand['concurso'],
                'indice_df': i,
                'similaridade': round(percentual, 1),
                'matches': matches,
                'assinatura': ass_cand, 
                'soma_real': ass_cand['soma_real'],
                'res_futuro': []
            })
            
    similares.sort(key=lambda x: (x['similaridade'], x['concurso']), reverse=True)
    
    return similares[:top_n], ass_alvo