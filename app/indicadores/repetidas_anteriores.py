from app.database import listar_sorteios

def contar_repetidas_anteriores(lista_dezenas):
    # Busca o último sorteio
    ultimo = listar_sorteios(1)[0]  # Retorna tupla: (Concurso, Data, Bola1, Bola2, ..., Bola6)
    dezenas_ultimo = set(ultimo[2:8])  # Extrai só as bolas/dezenas
    repetidas = [d for d in lista_dezenas if d in dezenas_ultimo]
    return f"{len(repetidas)} repetidas do último sorteio: {repetidas}"
