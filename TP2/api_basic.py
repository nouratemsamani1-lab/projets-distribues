from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'message': 'API TP2 - Bienvenue!'})

@app.route('/hello/<name>')
def hello(name):
    return jsonify({'message': f'Bonjour {name}!'})

@app.route('/api/add', methods=['POST'])
def add():
    data = request.json
    a = data.get('a', 0)
    b = data.get('b', 0)
    return jsonify({'resultat': a + b})

if __name__ == '__main__':
    app.run(debug=True, port=5000)