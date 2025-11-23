from .pares_impares import contar_pares_impares
from .primos import contar_primos
from .fibonacci import contar_fibonacci
from .sequenciais import contar_sequenciais
from .iniciais import contar_iniciais
from .finais import contar_finais
from .multiplos3 import contar_multiplos3
from .quadrantes import contar_quadrantes
from .repetidas_21 import contar_repetidas_21
from .repetidas_39 import contar_repetidas_39
from .repetidas_anteriores import contar_repetidas_anteriores

def calcular_indicadores(lista_dezenas, indicadores_escolhidos):
    resultados = {}
    # Exemplo para os indicadores mais simples
    if 'paresimpares' in indicadores_escolhidos:
        resultados['Par/Ímpar'] = contar_pares_impares(lista_dezenas)
    if 'primos' in indicadores_escolhidos:
        resultados['Primos'] = contar_primos(lista_dezenas)
    if 'fibonacci' in indicadores_escolhidos:
        resultados['Fibonacci'] = contar_fibonacci(lista_dezenas)
    if 'sequenciais' in indicadores_escolhidos:
        resultados['Sequenciais'] = contar_sequenciais(lista_dezenas)
    if 'iniciais' in indicadores_escolhidos:
        resultados['Mesmo início'] = contar_iniciais(lista_dezenas)
    if 'finais' in indicadores_escolhidos:
        resultados['Mesmo final'] = contar_finais(lista_dezenas)
    if 'multiplos3' in indicadores_escolhidos:
        resultados['Múltiplos de 3'] = contar_multiplos3(lista_dezenas)
    if 'quadrantes' in indicadores_escolhidos:
        resultados['Quadrantes'] = contar_quadrantes(lista_dezenas)
    if 'repetidas_anteriores' in indicadores_escolhidos:
        resultados['Repetidas do último'] = contar_repetidas_anteriores(lista_dezenas)
    if 'repetidas_39' in indicadores_escolhidos:
        resultados['Repetidas dos últimos 39'] = contar_repetidas_39(lista_dezenas)
    if 'repetidas_21' in indicadores_escolhidos:
        resultados['Repetidas dos últimos 21'] = contar_repetidas_21(lista_dezenas)
    return resultados
