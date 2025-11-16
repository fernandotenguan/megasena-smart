from flask import Flask, render_template, request, jsonify
from app.indicadores import calcular_indicadores

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/testar_indicadores', methods=['POST'])
def testar_indicadores():
    data = request.json
    dezenas = data.get('dezenas', [])
    indicadores = data.get('indicadores', [])
    resultado = calcular_indicadores(dezenas, indicadores)
    return jsonify(resultado)

if __name__ == "__main__":
    app.run(debug=True)
