
from flask import Flask, request, jsonify
import hashlib
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
tokens = {}

# BON HASH pour "password123"
PASSWORD_HASH = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"

USERS = {
    "alice": {
        "password_hash": PASSWORD_HASH,
        "role": "admin"
    },
    "bob": {
        "password_hash": PASSWORD_HASH,
        "role": "analyst"
    }
}

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    print(f"[LOGIN] Tentative: {username}")
    
    if username not in USERS:
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    received_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if received_hash != USERS[username]['password_hash']:
        print(f"[LOGIN] Hash incorrect pour {username}")
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    token = secrets.token_urlsafe(32)
    tokens[token] = {
        'username': username,
        'role': USERS[username]['role'],
        'expires': datetime.now() + timedelta(hours=24)
    }
    
    print(f"[LOGIN] ✅ Succès: {username}")
    return jsonify({
        'token': token,
        'role': USERS[username]['role'],
        'username': username
    })

@app.route('/auth/verify', methods=['POST'])
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token or token not in tokens:
        return jsonify({'valid': False}), 401
    
    if datetime.now() > tokens[token]['expires']:
        del tokens[token]
        return jsonify({'valid': False}), 401
    
    return jsonify({
        'valid': True,
        'username': tokens[token]['username'],
        'role': tokens[token]['role']
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("="*50)
    print("🔐 AUTH SERVICE CORRECT")
    print("Utilisateurs: alice, bob")
    print("Mot de passe: password123")
    print("="*50)
    app.run(host='localhost', port=8001, debug=False)