def contar_repetidas_21(lista_dezenas, ultimos21):
    todos = set(sum(ultimos21,[]))
    repetidas = [d for d in lista_dezenas if d in todos]
    return f"Repetidas últimos 21: {len(repetidas)} ({', '.join(map(str, repetidas))})"
