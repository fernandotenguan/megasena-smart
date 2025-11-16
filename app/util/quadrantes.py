import os

def carregar_quadrantes_csv(caminho=None):
    if caminho is None:
        caminho = os.path.join(os.path.dirname(__file__), '..', 'quadrantes.csv')
    quadrantes = {}
    with open(caminho, encoding='utf-8') as f:
        for linha in f:
            partes = linha.strip().split(',')
            quadrantes[partes[0]] = list(map(int, partes[1:]))
    return quadrantes

QUADRANTES = carregar_quadrantes_csv()
