def contar_multiplos3(lista_dezenas):
    mult3 = [d for d in lista_dezenas if d % 3 == 0]
    return f"Múltiplos de 3: {len(mult3)} ({', '.join(map(str,mult3))})"
