from flask import Flask, render_template, request, send_file
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar', methods=['POST'])
def gerar_combinacoes():
    parametros = request.json  # Recebe dados do frontend
    # Chame funções para criação combos, estatísticas, modelos preditivos
    return {'combinacoes': [], 'estatisticas': {}, 'modelos': {}}

@app.route('/exportar', methods=['POST'])
def exportar():
    # Gere o arquivo e envie
    return send_file('caminho_do_arquivo', as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
