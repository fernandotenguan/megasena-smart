# app/util/gerador.py
import random
from collections import defaultdict

# Definição dos Quadrantes (Mega-Sena 6x10)
Q1 = [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 21, 22, 23, 24, 25]
Q2 = [6, 7, 8, 9, 10, 16, 17, 18, 19, 20, 26, 27, 28, 29, 30]
Q3 = [31, 32, 33, 34, 35, 41, 42, 43, 44, 45, 51, 52, 53, 54, 55]
Q4 = [36, 37, 38, 39, 40, 46, 47, 48, 49, 50, 56, 57, 58, 59, 60]

def classificar_dezenas_por_quadrante(mapa_scores):
    potes = {'Q1': {}, 'Q2': {}, 'Q3': {}, 'Q4': {}}
    
    def classificar(lista_nums, label):
        lista_ordenada = sorted(lista_nums, key=lambda x: mapa_scores.get(x, 0), reverse=True)
        potes[label]['ouro'] = lista_ordenada[:5]
        potes[label]['prata'] = lista_ordenada[5:10]
        potes[label]['bronze'] = lista_ordenada[10:]

    if mapa_scores:
        classificar(Q1, 'Q1'); classificar(Q2, 'Q2')
        classificar(Q3, 'Q3'); classificar(Q4, 'Q4')
    else:
        potes['Q1']['ouro'] = Q1; potes['Q2']['ouro'] = Q2
        potes['Q3']['ouro'] = Q3; potes['Q4']['ouro'] = Q4
    
    return potes

def selecionar_5_balanceado(pote_quadrante):
    if not pote_quadrante.get('prata'): 
        return random.sample(pote_quadrante['ouro'], 5)

    r = random.random()
    selecao = []
    
    if r < 0.50: # Cenário A (Forte)
        selecao.extend(random.sample(pote_quadrante['ouro'], 3))
        selecao.extend(random.sample(pote_quadrante['prata'], 1))
        selecao.extend(random.sample(pote_quadrante['bronze'], 1))
    elif r < 0.80: # Cenário B (Equilibrado)
        selecao.extend(random.sample(pote_quadrante['ouro'], 2))
        selecao.extend(random.sample(pote_quadrante['prata'], 2))
        selecao.extend(random.sample(pote_quadrante['bronze'], 1))
    else: # Cenário C (Zebra)
        selecao.extend(random.sample(pote_quadrante['ouro'], 1))
        selecao.extend(random.sample(pote_quadrante['prata'], 2))
        selecao.extend(random.sample(pote_quadrante['bronze'], 2))
        
    return selecao

def validar_jogo_rigid(jogo, ultimo_sorteio):
    # 1. Repetidas (0 ou 1)
    rep = len(set(jogo).intersection(set(ultimo_sorteio)))
    if rep > 1: return False
    
    # 2. Sequenciais (Máximo 1 par)
    s = sorted(jogo)
    seqs = sum(1 for i in range(len(s)-1) if s[i+1] == s[i]+1)
    if seqs > 1: return False
    
    return True

def gerar_universo_filtrado(qtd_alvo, ultimo_sorteio, mapa_scores=None, modelo='F4'):
    """
    Gera o universo de jogos baseados no Modelo escolhido (F4 ou F5).
    """
    universo = set()
    potes = classificar_dezenas_por_quadrante(mapa_scores or {})
    
    # --- CONFIGURAÇÃO DO MODELO ---
    if modelo == 'F5':
        # Modelo F5 (Quina): Alta densidade por grupo, poucos grupos.
        # ~1500 jogos por grupo de 20.
        densidade_por_grupo = 1500
    else:
        # Modelo F4 (Quadra): Baixa densidade, muitos grupos (Padrão).
        # ~85 jogos por grupo de 20.
        densidade_por_grupo = 85

    # Cálculo de segurança para o loop não ficar infinito
    qtd_grupos_estimada = int(qtd_alvo / densidade_por_grupo) + 10
    max_tentativas_grupos = qtd_grupos_estimada * 10 
    
    tentativas = 0
    
    while len(universo) < qtd_alvo and tentativas < max_tentativas_grupos:
        tentativas += 1
        
        # 1. Montar Grupo de 20 (5 de cada Q)
        g20 = []
        g20.extend(selecionar_5_balanceado(potes['Q1']))
        g20.extend(selecionar_5_balanceado(potes['Q2']))
        g20.extend(selecionar_5_balanceado(potes['Q3']))
        g20.extend(selecionar_5_balanceado(potes['Q4']))
        
        # 2. Expansão baseada na Densidade do Modelo
        # Tenta gerar 'densidade_por_grupo' jogos VÁLIDOS dentro desse grupo
        jogos_gerados_neste_grupo = 0
        tentativas_internas = 0
        
        # Loop interno para extrair o máximo do grupo
        while jogos_gerados_neste_grupo < densidade_por_grupo and tentativas_internas < (densidade_por_grupo * 4):
            tentativas_internas += 1
            
            # Sorteia 6 dentro dos 20
            jogo = tuple(sorted(random.sample(g20, 6)))
            
            if jogo not in universo:
                if validar_jogo_rigid(jogo, ultimo_sorteio):
                    universo.add(jogo)
                    jogos_gerados_neste_grupo += 1
                    
            if len(universo) >= qtd_alvo: return list(universo)
    
    return list(universo)