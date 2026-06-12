"""
TP6.3 - API Sécurisée avec JWT, Rate Limiting et Validation
"""

from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
import hashlib
import re
import time
from collections import defaultdict
from threading import Lock
import uuid
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_cle_secrete_ici_changez_en_production'
app.config['JWT_EXPIRATION_HOURS'] = 24

# ============================================================
# STOCKAGE (SIMULATION)
# ============================================================

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

documents = {}
idempotency_store = {}
tokens_blacklist = set()

# ============================================================
# RATE LIMITING
# ============================================================

rate_limits = {
    '/auth/login': {'limit': 5, 'window': 60},
    '/documents': {'limit': 100, 'window': 60},
    '/search': {'limit': 30, 'window': 60},
    'default': {'limit': 50, 'window': 60}
}

request_counts = defaultdict(list)
rate_limit_lock = Lock()

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        endpoint = request.path
        config = rate_limits.get(endpoint, rate_limits['default'])
        limit = config['limit']
        window = config['window']
        
        client_ip = request.remote_addr
        key = f"{client_ip}:{endpoint}"
        
        with rate_limit_lock:
            now = time.time()
            request_counts[key] = [t for t in request_counts[key] if t > now - window]
            
            if len(request_counts[key]) >= limit:
                return jsonify({
                    'error': 'too_many_requests',
                    'message': f'Limite: {limit} requêtes par {window}s',
                    'retry_after': int(window - (now - request_counts[key][0]))
                }), 429
            
            request_counts[key].append(now)
        
        return f(*args, **kwargs)
    return decorated

# ============================================================
# VALIDATION
# ============================================================

def validate_uuid(uuid_string):
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return re.match(pattern, uuid_string) is not None

def validate_document(data):
    errors = []
    
    title = data.get('title', '').strip()
    if not title:
        errors.append("'title' requis")
    elif len(title) < 1 or len(title) > 200:
        errors.append("'title' doit faire 1-200 caractères")
    
    content = data.get('content', '').strip()
    if not content:
        errors.append("'content' requis")
    elif len(content) > 50000:
        errors.append("'content' max 50000 caractères")
    
    tags = data.get('tags', [])
    if not isinstance(tags, list):
        errors.append("'tags' doit être une liste")
    elif len(tags) > 10:
        errors.append("Maximum 10 tags")
    
    return errors

# ============================================================
# AUTHENTIFICATION
# ============================================================

def generate_token(username, role):
    return jwt.encode({
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=app.config['JWT_EXPIRATION_HOURS']),
        'iat': datetime.datetime.utcnow(),
        'jti': str(uuid.uuid4())
    }, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if token in tokens_blacklist:
            return None, "Token révoqué"
        return data, None
    except jwt.ExpiredSignatureError:
        return None, "Token expiré"
    except jwt.InvalidTokenError:
        return None, "Token invalide"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'unauthorized', 'message': 'Token manquant'}), 401
        
        user_data, error = verify_token(token)
        if error:
            return jsonify({'error': 'unauthorized', 'message': error}), 401
        
        request.user = user_data['username']
        request.user_role = user_data['role']
        request.token = token
        
        return f(*args, **kwargs)
    return decorated

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.user_role != required_role and request.user_role != 'admin':
                return jsonify({
                    'error': 'forbidden',
                    'message': f'Rôle {required_role} requis'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

# ============================================================
# ROUTES PUBLIQUES
# ============================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'documents_count': len(documents)
    })

# ============================================================
# ROUTES AUTH
# ============================================================

@app.route('/auth/login', methods=['POST'])
@rate_limit
def login():
    data = request.json
    
    if not data:
        return jsonify({'error': 'bad_request', 'message': 'Corps vide'}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'bad_request', 'message': 'username et password requis'}), 400
    
    if username not in users:
        return jsonify({'error': 'unauthorized', 'message': 'Identifiants invalides'}), 401
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != users[username]['password_hash']:
        return jsonify({'error': 'unauthorized', 'message': 'Identifiants invalides'}), 401
    
    token = generate_token(username, users[username]['role'])
    
    return jsonify({
        'token': token,
        'user_id': username,
        'role': users[username]['role'],
        'expires_in': app.config['JWT_EXPIRATION_HOURS'] * 3600
    })

@app.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    tokens_blacklist.add(request.token)
    return '', 204

# ============================================================
# ROUTES DOCUMENTS
# ============================================================

@app.route('/documents', methods=['POST'])
@token_required
@rate_limit
def create_document():
    idempotency_key = request.headers.get('Idempotency-Key')
    if not idempotency_key:
        return jsonify({'error': 'bad_request', 'message': 'Idempotency-Key requis'}), 400
    
    if idempotency_key in idempotency_store:
        return jsonify(idempotency_store[idempotency_key]), 200
    
    data = request.json
    if not data:
        return jsonify({'error': 'bad_request', 'message': 'Corps vide'}), 400
    
    errors = validate_document(data)
    if errors:
        return jsonify({'error': 'validation_error', 'errors': errors}), 400
    
    doc_id = str(uuid.uuid4())
    document = {
        'id': doc_id,
        'title': data['title'].strip(),
        'content': data['content'].strip(),
        'tags': data.get('tags', []),
        'author': request.user,
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat()
    }
    documents[doc_id] = document
    idempotency_store[idempotency_key] = document
    
    return jsonify(document), 201

@app.route('/documents', methods=['GET'])
@token_required
@rate_limit
def list_documents():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)
    
    doc_list = list(documents.values())
    start = (page - 1) * per_page
    end = start + per_page
    paginated = doc_list[start:end]
    
    return jsonify({
        'data': paginated,
        'pagination': {
            'total': len(doc_list),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(doc_list) + per_page - 1) // per_page
        }
    })

@app.route('/documents/<doc_id>', methods=['GET'])
@token_required
def get_document(doc_id):
    if not validate_uuid(doc_id):
        return jsonify({'error': 'bad_request', 'message': 'ID invalide'}), 400
    
    if doc_id not in documents:
        return jsonify({'error': 'not_found', 'message': 'Document non trouvé'}), 404
    
    document = documents[doc_id]
    
    if document['author'] != request.user and request.user_role != 'admin':
        return jsonify({'error': 'forbidden', 'message': 'Accès non autorisé'}), 403
    
    return jsonify(document)

@app.route('/documents/<doc_id>', methods=['PUT'])
@token_required
def update_document(doc_id):
    if not validate_uuid(doc_id):
        return jsonify({'error': 'bad_request', 'message': 'ID invalide'}), 400
    
    if doc_id not in documents:
        return jsonify({'error': 'not_found', 'message': 'Document non trouvé'}), 404
    
    document = documents[doc_id]
    
    if document['author'] != request.user and request.user_role != 'admin':
        return jsonify({'error': 'forbidden', 'message': 'Permission insuffisante'}), 403
    
    data = request.json
    if not data:
        return jsonify({'error': 'bad_request', 'message': 'Corps vide'}), 400
    
    errors = validate_document(data)
    if errors:
        return jsonify({'error': 'validation_error', 'errors': errors}), 400
    
    document['title'] = data['title'].strip()
    document['content'] = data['content'].strip()
    document['tags'] = data.get('tags', [])
    document['updated_at'] = datetime.datetime.now().isoformat()
    
    return jsonify(document)

@app.route('/documents/<doc_id>', methods=['DELETE'])
@token_required
def delete_document(doc_id):
    if not validate_uuid(doc_id):
        return jsonify({'error': 'bad_request', 'message': 'ID invalide'}), 400
    
    if doc_id not in documents:
        return jsonify({'error': 'not_found', 'message': 'Document non trouvé'}), 404
    
    document = documents[doc_id]
    
    if document['author'] != request.user and request.user_role != 'admin':
        return jsonify({'error': 'forbidden', 'message': 'Permission insuffisante'}), 403
    
    del documents[doc_id]
    
    return '', 204

# ============================================================
# ROUTES RECHERCHE
# ============================================================

@app.route('/search', methods=['GET'])
@token_required
@rate_limit
def search():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'error': 'bad_request', 'message': 'Paramètre q requis'}), 400
    
    results = []
    for doc_id, doc in documents.items():
        if query.lower() in doc['title'].lower() or query.lower() in doc['content'].lower():
            results.append({
                'id': doc_id,
                'title': doc['title'],
                'score': 1.0,
                'snippet': doc['content'][:200]
            })
    
    return jsonify({
        'results': results[:50],
        'total': len(results),
        'query': query
    })

# ============================================================
# ROUTES ADMIN
# ============================================================

@app.route('/admin/users', methods=['GET'])
@token_required
@role_required('admin')
def list_users():
    safe_users = {}
    for username, data in users.items():
        safe_users[username] = {
            'role': data['role'],
            'email': data['email']
        }
    return jsonify({'users': safe_users})

# ============================================================
# DÉMARRAGE
# ============================================================

if __name__ == '__main__':
    print("="*60)
    print("🔐 API Sécurisée - TP6.3")
    print("="*60)
    print("Utilisateurs: alice (admin), bob (user)")
    print("Mot de passe: password123")
    print("="*60)
    app.run(debug=True, port=5000)