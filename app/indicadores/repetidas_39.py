def contar_repetidas_39(lista_dezenas, ultimos39):
    todos = set(sum(ultimos39,[]))
    repetidas = [d for d in lista_dezenas if d in todos]
    return f"Repetidas últimos 39: {len(repetidas)} ({', '.join(map(str, repetidas))})"
