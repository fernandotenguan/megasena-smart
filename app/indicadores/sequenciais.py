def contar_sequenciais(lista_dezenas):
    ordenadas = sorted(lista_dezenas)
    seq2 = 0
    seq3 = 0
    i = 0
    while i < len(ordenadas)-1:
        if ordenadas[i]+1 == ordenadas[i+1]:
            count = 2
            while i+count-1 < len(ordenadas)-1 and ordenadas[i+count-1]+1 == ordenadas[i+count]:
                count += 1
            if count == 2:
                seq2 += 1
            elif count >= 3:
                seq3 += 1
            i += count-1
        i += 1
    return f"Sequenciais 2 seguidos: {seq2}, 3+ seguidos: {seq3}"
