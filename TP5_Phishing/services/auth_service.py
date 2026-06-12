@'
from flask import Flask, request, jsonify
import hashlib
import secrets
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)
tokens = {}

def load_users():
    """Charge les utilisateurs depuis le fichier JSON"""
    try:
        with open('storage/users.json', 'r') as f:
            users = json.load(f)
            print(f"[AUTH] Utilisateurs chargés: {list(users.keys())}")
            return users
    except Exception as e:
        print(f"[AUTH] Erreur chargement users: {e}")
        return {}

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    print(f"[AUTH] Tentative login: {username}")
    
    if not username or not password:
        return jsonify({'error': 'Identifiants requis'}), 400
    
    users = load_users()
    
    if username not in users:
        print(f"[AUTH] Utilisateur {username} non trouvé")
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    # Hash du mot de passe entré
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != users[username]['password_hash']:
        print(f"[AUTH] Mot de passe incorrect pour {username}")
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    # Génération du token
    token = secrets.token_urlsafe(32)
    tokens[token] = {
        'username': username,
        'role': users[username]['role'],
        'expires': datetime.now() + timedelta(hours=24)
    }
    
    print(f"[AUTH] Login réussi: {username} ({users[username]['role']})")
    return jsonify({
        'token': token,
        'role': users[username]['role'],
        'username': username
    })

@app.route('/auth/verify', methods=['POST'])
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token or token not in tokens:
        return jsonify({'valid': False}), 401
    
    token_data = tokens[token]
    if datetime.now() > token_data['expires']:
        del tokens[token]
        return jsonify({'valid': False}), 401
    
    return jsonify({
        'valid': True,
        'username': token_data['username'],
        'role': token_data['role']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("="*50)
    print("🔐 AUTH SERVICE")
    print("="*50)
    print(f"Dossier storage: {os.path.abspath('storage')}")
    print(f"Fichier users: {os.path.abspath('storage/users.json')}")
    print(f"Existe: {os.path.exists('storage/users.json')}")
    print("="*50)
    app.run(host='localhost', port=8001, debug=False)
'@ | Out-File -FilePath auth.py -Encoding UTF8