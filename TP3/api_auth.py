"""
TP3 - API REST avec Authentification JWT
Auteur: Projet Applications Distribuées
Date: 2026
"""

from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
import hashlib
import re

# ============================================================
# CONFIGURATION
# ============================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_tres_longue_et_complexe_2026'
app.config['TOKEN_EXPIRATION_HOURS'] = 24

# ============================================================
# BASE DE DONNÉES (en mémoire)
# ============================================================

# Utilisateurs avec mots de passe hashés
users = {
    'alice': {
        'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),
        'role': 'admin',
        'email': 'alice@example.com'
    },
    'bob': {
        'password_hash': hashlib.sha256('password123'.encode()).hexdigest(),
        'role': 'user',
        'email': 'bob@example.com'
    }
}

# Stockage des tokens révoqués (blacklist)
revoked_tokens = set()

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def validate_email(email):
    """Valide le format d'un email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def hash_password(password):
    """Hash un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================================
# DÉCORATEUR D'AUTHENTIFICATION
# ============================================================

def token_required(f):
    """
    Décorateur pour protéger les routes nécessitant une authentification
    Vérifie la présence et la validité du token JWT
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Récupérer le token du header Authorization
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        
        # Vérifier si le token existe
        if not token:
            return jsonify({
                'error': 'Token manquant',
                'message': 'Veuillez fournir un token JWT dans le header Authorization'
            }), 401
        
        # Vérifier si le token est révoqué
        if token in revoked_tokens:
            return jsonify({
                'error': 'Token révoqué',
                'message': 'Ce token a été invalidé'
            }), 401
        
        try:
            # Décoder et vérifier le token
            data = jwt.decode(
                token, 
                app.config['SECRET_KEY'], 
                algorithms=['HS256']
            )
            request.user = data['username']
            request.user_role = data.get('role', 'user')
            request.token_data = data
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': 'Token expiré',
                'message': 'Veuillez vous reconnecter'
            }), 401
            
        except jwt.InvalidTokenError:
            return jsonify({
                'error': 'Token invalide',
                'message': 'Le token fourni est invalide'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated

# ============================================================
# DÉCORATEUR DE RÔLE
# ============================================================

def role_required(required_role):
    """
    Décorateur pour vérifier les rôles
    À utiliser APRÈS @token_required
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.user_role != required_role and request.user_role != 'admin':
                return jsonify({
                    'error': 'Permission refusée',
                    'message': f'Rôle {required_role} requis'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============================================================
# ROUTES PUBLIQUES
# ============================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Vérification de l'état du service"""
    return jsonify({
        'status': 'healthy',
        'service': 'TP3 - API Authentification',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '1.0'
    })

@app.route('/', methods=['GET'])
def home():
    """Page d'accueil de l'API"""
    return jsonify({
        'message': 'Bienvenue sur l\'API du TP3',
        'endpoints': {
            'public': [
                {'method': 'GET', 'path': '/', 'description': 'Cette page'},
                {'method': 'GET', 'path': '/health', 'description': 'Health check'},
                {'method': 'POST', 'path': '/auth/login', 'description': 'Connexion'},
                {'method': 'POST', 'path': '/auth/register', 'description': 'Inscription'}
            ],
            'protected': [
                {'method': 'GET', 'path': '/api/protected', 'description': 'Zone protégée'},
                {'method': 'GET', 'path': '/api/profile', 'description': 'Profil utilisateur'},
                {'method': 'POST', 'path': '/api/logout', 'description': 'Déconnexion'}
            ],
            'admin': [
                {'method': 'GET', 'path': '/admin/users', 'description': 'Liste des utilisateurs'}
            ]
        }
    })

# ============================================================
# ROUTES D'AUTHENTIFICATION
# ============================================================

@app.route('/auth/login', methods=['POST'])
def login():
    """
    Authentification d'un utilisateur
    Retourne un token JWT
    """
    data = request.json
    
    # Validation des champs
    if not data:
        return jsonify({'error': 'Corps de requête vide'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'error': 'Champs manquants',
            'message': 'Les champs username et password sont requis'
        }), 400
    
    # Vérifier si l'utilisateur existe
    if username not in users:
        return jsonify({
            'error': 'Identifiants invalides',
            'message': 'Nom d\'utilisateur ou mot de passe incorrect'
        }), 401
    
    # Vérifier le mot de passe
    password_hash = hash_password(password)
    
    if password_hash != users[username]['password_hash']:
        return jsonify({
            'error': 'Identifiants invalides',
            'message': 'Nom d\'utilisateur ou mot de passe incorrect'
        }), 401
    
    # Créer le token JWT
    token = jwt.encode({
        'username': username,
        'role': users[username]['role'],
        'email': users[username]['email'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=app.config['TOKEN_EXPIRATION_HOURS']),
        'iat': datetime.datetime.utcnow()  # Issued at
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    # Journaliser la connexion
    print(f"[LOG] Connexion réussie: {username} à {datetime.datetime.now()}")
    
    return jsonify({
        'success': True,
        'token': token,
        'username': username,
        'role': users[username]['role'],
        'message': f'Bienvenue {username} !',
        'expires_in': app.config['TOKEN_EXPIRATION_HOURS'] * 3600  # en secondes
    })

@app.route('/auth/register', methods=['POST'])
def register():
    """
    Inscription d'un nouvel utilisateur
    """
    data = request.json
    
    # Validation des champs
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({
            'error': 'Champs manquants',
            'message': 'username, password et email sont requis'
        }), 400
    
    # Vérifier si l'utilisateur existe déjà
    if username in users:
        return jsonify({
            'error': 'Utilisateur existe',
            'message': f'Le nom {username} est déjà pris'
        }), 409
    
    # Valider l'email
    if not validate_email(email):
        return jsonify({
            'error': 'Email invalide',
            'message': 'Veuillez fournir un email valide'
        }), 400
    
    # Vérifier la force du mot de passe
    if len(password) < 6:
        return jsonify({
            'error': 'Mot de passe trop faible',
            'message': 'Le mot de passe doit contenir au moins 6 caractères'
        }), 400
    
    # Créer l'utilisateur
    users[username] = {
        'password_hash': hash_password(password),
        'role': 'user',  # Par défaut, rôle user
        'email': email
    }
    
    print(f"[LOG] Nouvel utilisateur inscrit: {username}")
    
    return jsonify({
        'success': True,
        'message': f'Utilisateur {username} créé avec succès',
        'username': username,
        'role': 'user'
    }), 201

# ============================================================
# ROUTES PROTÉGÉES
# ============================================================

@app.route('/api/protected', methods=['GET'])
@token_required
def protected_zone():
    """
    Route protégée nécessitant un token valide
    """
    return jsonify({
        'message': f'Bienvenue dans la zone protégée {request.user} !',
        'data': 'Ceci est une information confidentielle',
        'user': request.user,
        'role': request.user_role,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    """
    Récupère le profil de l'utilisateur connecté
    """
    user_data = users.get(request.user, {})
    
    return jsonify({
        'username': request.user,
        'role': request.user_role,
        'email': user_data.get('email'),
        'authenticated_at': request.token_data.get('iat'),
        'token_expires': request.token_data.get('exp')
    })

@app.route('/api/logout', methods=['POST'])
@token_required
def logout():
    """
    Déconnexion - Ajoute le token à la blacklist
    """
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')
    
    # Ajouter le token à la blacklist
    revoked_tokens.add(token)
    
    print(f"[LOG] Déconnexion: {request.user}")
    
    return jsonify({
        'success': True,
        'message': 'Déconnecté avec succès'
    })

# ============================================================
# ROUTES ADMIN
# ============================================================

@app.route('/admin/users', methods=['GET'])
@token_required
@role_required('admin')
def list_users():
    """
    Liste tous les utilisateurs (réservé aux admins)
    """
    # Ne pas renvoyer les mots de passe
    safe_users = {}
    for username, data in users.items():
        safe_users[username] = {
            'role': data['role'],
            'email': data['email']
        }
    
    return jsonify({
        'users': safe_users,
        'total': len(safe_users),
        'admin': request.user
    })

@app.route('/admin/users/<username>', methods=['DELETE'])
@token_required
@role_required('admin')
def delete_user(username):
    """
    Supprime un utilisateur (réservé aux admins)
    """
    if username not in users:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    if username == request.user:
        return jsonify({'error': 'Vous ne pouvez pas vous supprimer vous-même'}), 400
    
    del users[username]
    
    print(f"[LOG] Utilisateur supprimé par {request.user}: {username}")
    
    return jsonify({
        'success': True,
        'message': f'Utilisateur {username} supprimé'
    })

# ============================================================
# DÉMARRAGE DE L'APPLICATION
# ============================================================

if __name__ == '__main__':
    print("="*60)
    print("🔐 TP3 - API REST avec Authentification JWT")
    print("="*60)
    print(f"📅 Démarrage: {datetime.datetime.now()}")
    print(f"🔑 Clé secrète: {app.config['SECRET_KEY'][:10]}...")
    print(f"⏰ Expiration token: {app.config['TOKEN_EXPIRATION_HOURS']} heures")
    print("-"*60)
    print("👥 Utilisateurs disponibles:")
    for username, data in users.items():
        print(f"   • {username} (mot de passe: password123) - Rôle: {data['role']}")
    print("-"*60)
    print("🚀 Serveur démarré sur http://localhost:5000")
    print("📡 Routes disponibles:")
    print("   GET  /                 - Page d'accueil")
    print("   GET  /health           - Health check")
    print("   POST /auth/login       - Connexion")
    print("   POST /auth/register    - Inscription")
    print("   GET  /api/protected    - Zone protégée (token requis)")
    print("   GET  /api/profile      - Profil (token requis)")
    print("   POST /api/logout       - Déconnexion (token requis)")
    print("   GET  /admin/users      - Liste users (admin seulement)")
    print("="*60)
    
    app.run(debug=True, port=5000)