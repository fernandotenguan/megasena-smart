# app/util/simulation.py
import pandas as pd
import time
import random
from collections import defaultdict, Counter
from .config_mega import NUM_DEZENAS_SORTEADAS
from .analise_preditiva import gerar_perfil_preditivo_completo, extrair_perfil_alvo_completo
from .gerador import gerar_universo_filtrado
from .pontuacao import calcular_pontuacao_binaria

def simular_cenario_passado(df_completo, concurso_simulacao_id, params):
    """
    params: dict com chaves 'qtd', 's1', 'p1', ... 'pressao'
    """
    start_time = time.time()
    
    # 1. Preparação dos Dados (Corte Temporal)
    idx_mask = df_completo.index[df_completo['Concurso'] == concurso_simulacao_id].tolist()
    if not idx_mask: return {'erro': 'Concurso não encontrado'}
    idx_corte = idx_mask[0]
    
    df_treino = df_completo.iloc[:idx_corte+1] 
    
    if idx_corte + 1 >= len(df_completo):
        return {'erro': 'Este é o último concurso, impossível validar futuro.'}
        
    linha_futuro = df_completo.iloc[idx_corte + 1]
    cols = [f'Bola{i}' for i in range(1, NUM_DEZENAS_SORTEADAS + 1)]
    resultado_real = linha_futuro[cols].dropna().astype(int).tolist()
    ultimo_sorteio = df_treino.iloc[-1][cols].dropna().astype(int).tolist()

    # 2. MOTOR PREDITIVO (Treinado no Passado)
    predicao = gerar_perfil_preditivo_completo(df_treino)
    perfil_alvo_raw = extrair_perfil_alvo_completo(predicao)
    
    gabarito = {}
    for k in perfil_alvo_raw:
        gabarito[k] = {'alvo': perfil_alvo_raw[k]}
        if 'limites' in predicao.get(k, {}):
            gabarito[k]['limites'] = predicao[k]['limites']

    # 3. GERAÇÃO (Pool)
    # Aumentei para 50k para ter margem para os filtros
    candidatos = gerar_universo_filtrado(300000, ultimo_sorteio)
    
    # 4. PONTUAÇÃO E SELEÇÃO (Lógica Fiel ao Modelo V5)
    mapa39 = predicao['mapa_39']
    mapa21 = predicao['mapa_21']
    
    baldes = defaultdict(list)
    scores_audit = []
    
    for jogo in candidatos:
        score = calcular_pontuacao_binaria(jogo, gabarito, mapa39, mapa21)
        baldes[score].append(jogo)
        scores_audit.append(score)
        
    max_score_found = max(scores_audit) if scores_audit else 0
    
    # --- INÍCIO DA LÓGICA DE SELEÇÃO POR METAS ---
    finalistas = []
    dezenas_pressao = predicao['ciclo_faltantes'].union(predicao['atrasadas_criticas'])
    uso_global = Counter()
    
    qtd_meta = params.get('qtd', 20)
    perc_pressao = params.get('pressao', 60)
    
    # Configurações de Metas (Cascata)
    metas = [
        (params.get('s1', 12), params.get('p1', 20)),
        (params.get('s2', 11), params.get('p2', 30)),
        (params.get('s3', 10), params.get('p3', 30)),
        (params.get('s4', 9),  params.get('p4', 20))
    ]

    def selecionar_com_diversificacao(nota_alvo, qtd_necessaria, lista_existente):
        pool_nota = baldes[nota_alvo]
        if not pool_nota: return []
        random.shuffle(pool_nota)
        selecionados_agora = []
        
        # Tentativa 1: Respeitando filtros de diversificação e pressão
        for jogo in pool_nota:
            if len(selecionados_agora) >= qtd_necessaria: break
            if jogo in lista_existente: continue
            
            # Filtro de Pressão
            tem_pressao = bool(set(jogo).intersection(dezenas_pressao))
            if perc_pressao > 0 and not tem_pressao:
                # Se exige pressão e jogo não tem, descarta com chance baseada na %
                if random.random() * 100 < perc_pressao: continue

            # Filtro de Repetição Visual (Diversificação)
            pontos_repeticao = sum([uso_global[d] for d in jogo])
            if pontos_repeticao < 25: 
                selecionados_agora.append(jogo)
                for d in jogo: uso_global[d] += 1
        
        # Tentativa 2: Se faltou jogo, pega qualquer um da nota (relaxa filtros)
        if len(selecionados_agora) < qtd_necessaria:
            for jogo in pool_nota:
                if len(selecionados_agora) >= qtd_necessaria: break
                if jogo not in lista_existente and jogo not in selecionados_agora:
                    selecionados_agora.append(jogo)
                    for d in jogo: uso_global[d] += 1
                    
        return selecionados_agora

    # Executa a Cascata
    for meta_score, meta_perc in metas:
        falta = qtd_meta - len(finalistas)
        if falta <= 0: break
        cota = int(qtd_meta * (meta_perc/100))
        finalistas.extend(selecionar_com_diversificacao(meta_score, cota, finalistas))

    # Preenchimento de Sobras (Waterfall descrecente)
    if len(finalistas) < qtd_meta:
        for sc in range(max_score_found, -1, -1):
            if len(finalistas) >= qtd_meta: break
            # Pula os scores já processados nas metas principais para não duplicar lógica (opcional)
            falta = qtd_meta - len(finalistas)
            finalistas.extend(selecionar_com_diversificacao(sc, falta, finalistas))
            
    jogos_finais = finalistas[:qtd_meta]
    
    # 5. CONFERÊNCIA
    acertos_stats = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
    lista_jogos = []
    
    for jogo in jogos_finais:
        # Recalcula score final apenas para exibição
        score = calcular_pontuacao_binaria(jogo, gabarito, mapa39, mapa21)
        acertos = len(set(jogo).intersection(set(resultado_real)))
        acertos_stats[acertos] += 1
        lista_jogos.append({
            'numeros': jogo,
            'score': score,
            'acertos': acertos
        })
    
    # Ordena para exibição: Quem acertou mais fica no topo
    lista_jogos.sort(key=lambda x: (x['acertos'], x['score']), reverse=True)
        
    return {
        'concurso_base': int(concurso_simulacao_id),
        'concurso_validacao': int(linha_futuro['Concurso']),
        'resultado_real': resultado_real,
        'resumo': acertos_stats,
        'jogos': lista_jogos,
        'tempo': round(time.time() - start_time, 2),
        'max_score_epoca': max_score_found
    }