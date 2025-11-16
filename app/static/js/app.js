const { createApp } = Vue;

createApp({
  data() {
    return {
      message: "Se você vê este texto, Vue está funcionando!",
      resultado: "",
    };
  },
  methods: {
    testarVue() {
      this.resultado = "Frontend Vue está OK!";
    },
  },
  delimiters: ["[[", "]]"], // repare nos colchetes em vez de chaves
}).mount("#app");
