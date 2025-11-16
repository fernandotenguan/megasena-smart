def contar_iniciais(lista_dezenas):
    # Ex: 01,06,07 - início 0
    inicio = [str(d).zfill(2)[0] for d in lista_dezenas]
    contagem = {i:inicio.count(i) for i in set(inicio)}
    mais_frequente = max(contagem, key=contagem.get)
    return f"Números com início '{mais_frequente}': {contagem[mais_frequente]}"
