from .pares_impares import contar_pares_impares
# from .primos import contar_primos
# Continue assim para todos

def calcular_indicadores(lista_dezenas, indicadores_escolhidos):
    resultados = {}
    if 'pares_impares' in indicadores_escolhidos:
        resultados['pares_impares'] = contar_pares_impares(lista_dezenas)
    # Adicione mais conforme evolução
    return resultados
