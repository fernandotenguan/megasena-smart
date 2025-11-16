from app.util.quadrantes import QUADRANTES

def contar_quadrantes(lista_dezenas):
    grupos = {q:0 for q in QUADRANTES}
    for d in lista_dezenas:
        for q, nums in QUADRANTES.items():
            if d in nums:
                grupos[q] += 1
    return f"Q1: {grupos['Q1']}, Q2: {grupos['Q2']}, Q3: {grupos['Q3']}, Q4: {grupos['Q4']}"
