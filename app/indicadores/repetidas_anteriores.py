# Exige passar o ultimo_sorteio na função!
def contar_repetidas_anteriores(lista_dezenas, ultimo_sorteio):
    repetidas = [d for d in lista_dezenas if d in ultimo_sorteio]
    return f"Repetidas do último sorteio: {len(repetidas)} ({', '.join(map(str,repetidas))})"
