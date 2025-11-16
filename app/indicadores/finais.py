def contar_finais(lista_dezenas):
    # Ex: 14,24,54 - final 4
    final = [str(d).zfill(2)[-1] for d in lista_dezenas]
    contagem = {f:final.count(f) for f in set(final)}
    mais_frequente = max(contagem, key=contagem.get)
    return f"Números com final '{mais_frequente}': {contagem[mais_frequente]}"
