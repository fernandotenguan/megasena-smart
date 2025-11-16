def gerar_fibonacci(limite=60):
    fib = [0, 1]
    while fib[-1] < limite:
        fib.append(fib[-1]+fib[-2])
    return set(fib)

def contar_fibonacci(lista_dezenas):
    fibonacci = gerar_fibonacci()
    fibos = [d for d in lista_dezenas if d in fibonacci]
    return f"Fibonacci: {len(fibos)} ({', '.join(map(str,fibos))})"
