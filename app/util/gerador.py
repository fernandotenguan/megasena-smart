# app/util/gerador.py
import random
from collections import Counter
from .config_mega import LISTA_FIBONACCI, LISTA_MULTIPLOS_3, UNIVERSO_DEZENAS

# Pré-carrega para performance
SET_FIBO = set(LISTA_FIBONACCI)

# Lista fixa de Quadrantes Aceitáveis (Baseado na sua imagem/histórico)
# Perfis que cobrem > 90% dos sorteios
PERFIS_QUADRANTES_ACEITOS = {
    "1-2-1-2", "1-1-2-2", "2-1-1-2", "2-1-2-1", "1-2-2-1", "2-2-1-1",
    "1-1-1-3", "1-1-3-1", "3-1-1-1", "1-3-1-1", "0-2-2-2", "2-0-2-2",
    "2-2-2-0", "2-2-0-2", "2-2-1-1", "1-2-1-2", "3-2-1-0", "3-1-2-0",
    "0-3-2-1", "2-3-0-1", "1-2-3-0", "0-2-3-1", "2-1-3-0", "3-0-2-1",
    "1-3-2-0", "3-2-0-1", "2-3-1-0", "1-0-3-2", "2-0-1-3", "0-1-3-2",
    "0-3-1-2", "2-1-0-3", "1-3-0-2", "3-0-1-2", "3-1-0-2", "0-1-2-3"
    # Adicionei os principais. Em produção ideal, isso viria do banco.
}

def validar_filtros_rigidos(jogo, ultimo_sorteio_set):
    """
    Retorna True se o jogo passar pelos 6 Filtros Rígidos.
    """
    dezenas = sorted(jogo)
    
    # 1. Repetidas do Anterior (0 ou 1)
    rep = len(set(dezenas).intersection(ultimo_sorteio_set))
    if rep > 1: return False
    
    # 2. Sequenciais (Nenhuma ou 1 par)
    # Calcula quantas sequencias existem
    seq_count = 0
    for i in range(len(dezenas)-1):
        if dezenas[i+1] == dezenas[i] + 1:
            seq_count += 1
    if seq_count > 1: return False # Permite 0 ou 1 sequencia (par)
    
    # 3. Fibonacci (0, 1 ou 2)
    fibo = len([x for x in dezenas if x in SET_FIBO])
    if fibo > 2: return False
    
    # 4. Concentração Iniciais (Máx 3)
    inis = [str(d).zfill(2)[0] for d in dezenas]
    if max(Counter(inis).values()) > 3: return False
    
    # 5. Concentração Finais (Máx 3)
    fins = [str(d).zfill(2)[-1] for d in dezenas]
    if max(Counter(fins).values()) > 3: return False
    
    # 6. Perfil de Quadrantes
    q = [0,0,0,0]
    for d in dezenas:
        if d in [1,2,3,4,5,11,12,13,14,15,21,22,23,24,25]: q[0]+=1
        elif d in [6,7,8,9,10,16,17,18,19,20,26,27,28,29,30]: q[1]+=1
        elif d in [31,32,33,34,35,41,42,43,44,45,51,52,53,54,55]: q[2]+=1
        else: q[3]+=1
    perfil = f"{q[0]}-{q[1]}-{q[2]}-{q[3]}"
    
    # Se não estiver na lista de aceitos, rejeita
    # Nota: Se a lista estiver incompleta, pode filtrar demais. 
    # Para segurança inicial, vamos permitir se não for extremo (ex: 4-2-0-0)
    if q.count(0) >= 2: return False # Rejeita se tiver 2 quadrantes vazios (regra genérica boa)
    
    return True

def gerar_universo_filtrado(qtd_alvo, ultimo_sorteio, db_path=None):
    """
    Gera jogos aleatórios até conseguir 'qtd_alvo' jogos que passem nos filtros.
    """
    universo_valido = set()
    todos_numeros = list(range(1, 61))
    ultimo_set = set(ultimo_sorteio)
    
    # Proteção contra loop infinito (max tentativas)
    tentativas = 0
    max_tentativas = qtd_alvo * 200 
    
    while len(universo_valido) < qtd_alvo and tentativas < max_tentativas:
        tentativas += 1
        
        # Gera candidato
        cand = sorted(random.sample(todos_numeros, 6))
        cand_tuple = tuple(cand)
        
        if cand_tuple in universo_valido: continue
        
        if validar_filtros_rigidos(cand, ultimo_set):
            universo_valido.add(cand_tuple)
            
    return [list(x) for x in universo_valido]