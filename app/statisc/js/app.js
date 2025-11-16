const { createApp } = Vue;

createApp({
  data() {
    return {
      indicadoresSelecionados: [],
      quantidadeCombinacoes: 10,
      estilosSelecionados: [],
      exportTipo: "csv",
      // Adicione outros campos conforme for evoluindo
    };
  },
  methods: {
    gerarCombinacoes() {
      // Chamar backend Flask com seleção atual
    },
    exportarResultados(tipo) {
      // Requisição ao backend, passando tipo desejado
    },
  },
}).mount("#app");
