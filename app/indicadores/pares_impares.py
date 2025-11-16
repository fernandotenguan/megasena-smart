def contar_pares_impares(lista_dezenas):
    pares = sum(1 for d in lista_dezenas if d % 2 == 0)
    impares = len(lista_dezenas) - pares
    return {'pares': pares, 'impares': impares}
