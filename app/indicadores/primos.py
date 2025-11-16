def eh_primo(n):
    if n < 2: return False
    for i in range(2, int(n**0.5)+1):
        if n % i == 0:
            return False
    return True

def contar_primos(lista_dezenas):
    primos = [d for d in lista_dezenas if eh_primo(d)]
    return f"Primos: {len(primos)} ({', '.join(map(str,primos))})"
