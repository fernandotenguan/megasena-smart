from app.database import listar_sorteios

def contar_repetidas_21(lista_dezenas):
    ultimos21 = listar_sorteios(21)
    contagem = {d: 0 for d in lista_dezenas}
    # Conta quantas vezes cada dezena aparece nos sorteios
    for sorteio in ultimos21:
        dezenas_sorteio = sorteio[2:8]
        for d in lista_dezenas:
            if d in dezenas_sorteio:
                contagem[d] += 1
    # Exemplo de resposta: {12: 3, 18: 0, 44: 1, ...}
    return f"Contagem nos últimos 21 sorteios: {contagem}"

