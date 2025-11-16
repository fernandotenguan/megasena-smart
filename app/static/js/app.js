const { createApp } = Vue;

createApp({
  data() {
    return {
      dezenasStr: "",
      indicadoresDisponiveis: [
        { valor: "paresimpares", label: "Par/Ímpar" },
        { valor: "primos", label: "Primos" },
        { valor: "fibonacci", label: "Fibonacci" },
        { valor: "sequenciais", label: "Sequenciais (2 e 3 seguidos)" },
        { valor: "iniciais", label: "Mesmo início" },
        { valor: "finais", label: "Mesmo final" },
        { valor: "multiplos3", label: "Múltiplos de 3" },
        {
          valor: "repetidas_anteriores",
          label: "Repetidas do sorteio anterior",
        },
        { valor: "repetidas_21", label: "Repetidas últimos 21 sorteios" },
        { valor: "repetidas_39", label: "Repetidas últimos 39 sorteios" },
        { valor: "quadrantes", label: "Quadrantes" },
      ],
      indicadoresSelecionados: [],
      resultadoIndicadores: {},
    };
  },
  methods: {
    async testarIndicadores() {
      const dezenas = this.dezenasStr
        .split(/[ ,]+/)
        .map((d) => parseInt(d))
        .filter((d) => !isNaN(d));
      // Chama backend Flask passando os indicadores escolhidos e as dezenas
      const response = await fetch("/api/testar_indicadores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dezenas,
          indicadores: this.indicadoresSelecionados,
        }),
      });
      const data = await response.json();
      this.resultadoIndicadores = data;
    },
  },
}).mount("#app");
