from app.database import listar_sorteios

def contar_repetidas_39(lista_dezenas):
    ultimos39 = listar_sorteios(39)
    contagem = {d: 0 for d in lista_dezenas}
    for sorteio in ultimos39:
        dezenas_sorteio = sorteio[2:8]
        for d in lista_dezenas:
            if d in dezenas_sorteio:
                contagem[d] += 1
    return f"Contagem nos últimos 39 sorteios: {contagem}"

