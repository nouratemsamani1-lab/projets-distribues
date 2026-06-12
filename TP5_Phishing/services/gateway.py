from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime
from functools import wraps
import time

app = Flask(__name__)

# Configuration des services
SERVICES = {
    'auth': 'http://localhost:8001',
    'analysis': 'http://localhost:8002',
    'audit': 'http://localhost:8003'
}

TIMEOUT = 5  # seconds
MAX_SUBMISSION_SIZE = 50000

# Stockage local
SUBMISSIONS_FILE = 'storage/submissions.json'
submission_counter = 1

def load_submissions():
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_submissions(submissions):
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(submissions, f, indent=2)

def log_audit(event_type, username, action, details=None):
    """Envoi asynchrone vers audit service"""
    try:
        requests.post(
            f"{SERVICES['audit']}/audit/log",
            json={
                'event_type': event_type,
                'username': username,
                'action': action,
                'details': details or {}
            },
            timeout=1  # Court timeout, ne pas bloquer
        )
    except:
        pass  # Log local en cas d'échec

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Authentification requise'}), 401
        
        try:
            resp = requests.post(
                f"{SERVICES['auth']}/auth/verify",
                headers={'Authorization': f'Bearer {token}'},
                timeout=TIMEOUT
            )
            
            if resp.status_code != 200:
                return jsonify({'error': 'Token invalide'}), 401
            
            user_data = resp.json()
            request.user = user_data
            return f(*args, **kwargs)
            
        except requests.Timeout:
            return jsonify({'error': 'Service indisponible'}), 503
        except:
            return jsonify({'error': 'Erreur authentification'}), 500
    
    return decorated

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.user.get('role') != role and request.user.get('role') != 'admin':
                log_audit('UNAUTHORIZED_ACCESS', request.user.get('username'), f'Accès refusé à {request.path}')
                return jsonify({'error': 'Permission insuffisante'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/auth/login', methods=['POST'])
def login():
    """Proxy vers auth service"""
    try:
        resp = requests.post(
            f"{SERVICES['auth']}/auth/login",
            json=request.json,
            timeout=TIMEOUT
        )
        return jsonify(resp.json()), resp.status_code
    except requests.Timeout:
        return jsonify({'error': 'Service authentification indisponible'}), 503

@app.route('/submissions', methods=['POST'])
@require_auth
def submit_email():
    """Soumettre un email suspect"""
    data = request.json
    
    # Validation entrées
    required = ['sender', 'subject', 'content']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Champ manquant: {field}'}), 400
    
    # Limitation taille
    if len(data.get('content', '')) > MAX_SUBMISSION_SIZE:
        return jsonify({'error': 'Contenu trop long'}), 400
    
    # Nettoyage basique
    data['sender'] = data['sender'][:200]
    data['subject'] = data['subject'][:200]
    data['content'] = data['content'][:MAX_SUBMISSION_SIZE]
    
    try:
        # Appel analysis service avec timeout
        analysis_resp = requests.post(
            f"{SERVICES['analysis']}/analyze",
            json=data,
            timeout=TIMEOUT
        )
        
        if analysis_resp.status_code != 200:
            return jsonify({'error': 'Erreur analyse'}), 500
        
        analysis = analysis_resp.json()
        
        # Stockage
        global submission_counter
        submissions = load_submissions()
        submission = {
            'id': len(submissions) + 1,
            'submitted_by': request.user['username'],
            'timestamp': datetime.now().isoformat(),
            **data,
            'analysis': analysis
        }
        submissions.append(submission)
        save_submissions(submissions)
        
        # Audit
        log_audit('SUBMISSION', request.user['username'], 'Email soumis', {
            'id': submission['id'],
            'risk': analysis['risk_level']
        })
        
        return jsonify({
            'id': submission['id'],
            'risk_level': analysis['risk_level'],
            'risk_score': analysis['risk_score'],
            'reasons': analysis['reasons']
        }), 201
        
    except requests.Timeout:
        log_audit('ERROR', request.user['username'], 'Timeout analysis service')
        return jsonify({'error': 'Service analyse indisponible'}), 503
    except Exception as e:
        log_audit('ERROR', request.user['username'], f'Erreur: {str(e)}')
        return jsonify({'error': 'Erreur interne'}), 500

@app.route('/submissions', methods=['GET'])
@require_auth
def list_submissions():
    """Lister les signalements (filtrage selon rôle)"""
    submissions = load_submissions()
    
    # Filtrage
    search = request.args.get('search')
    score_filter = request.args.get('score')
    sender_filter = request.args.get('sender')
    
    result = submissions.copy()
    
    if search:
        result = [s for s in result if 
                 search.lower() in s['subject'].lower() or 
                 search.lower() in s['content'].lower()]
    
    if score_filter:
        result = [s for s in result if s['analysis']['risk_level'] == score_filter.upper()]
    
    if sender_filter:
        result = [s for s in result if sender_filter.lower() in s['sender'].lower()]
    
    # Admin voit tout, analyste voit seulement ses soumissions
    if request.user['role'] != 'admin':
        result = [s for s in result if s['submitted_by'] == request.user['username']]
    
    # Ne pas renvoyer tout le contenu
    for r in result:
        if 'content' in r:
            r['content_preview'] = r['content'][:200] + ('...' if len(r['content']) > 200 else '')
            del r['content']
    
    return jsonify({'submissions': result[-50:]})  # 50 derniers max

@app.route('/submissions/<int:submission_id>', methods=['GET'])
@require_auth
def get_submission(submission_id):
    submissions = load_submissions()
    submission = next((s for s in submissions if s['id'] == submission_id), None)
    
    if not submission:
        return jsonify({'error': 'Signalement non trouvé'}), 404
    
    # Vérification droits
    if request.user['role'] != 'admin' and submission['submitted_by'] != request.user['username']:
        log_audit('UNAUTHORIZED_ACCESS', request.user['username'], f'Accès refusé submission {submission_id}')
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    log_audit('VIEW', request.user['username'], f'Consultation submission {submission_id}')
    return jsonify(submission)

@app.route('/admin/logs', methods=['GET'])
@require_auth
@require_role('admin')
def get_audit_logs():
    """Accès admin aux logs"""
    try:
        resp = requests.get(
            f"{SERVICES['audit']}/audit/logs",
            params=request.args,
            timeout=TIMEOUT
        )
        return jsonify(resp.json()), resp.status_code
    except requests.Timeout:
        return jsonify({'error': 'Service audit indisponible'}), 503

@app.route('/health', methods=['GET'])
def health():
    """Health check de tous les services"""
    health_status = {}
    for name, url in SERVICES.items():
        try:
            resp = requests.get(f"{url}/health", timeout=2)
            health_status[name] = 'healthy' if resp.status_code == 200 else 'unhealthy'
        except:
            health_status[name] = 'unavailable'
    
    return jsonify(health_status)

if __name__ == '__main__':
    import os
    os.makedirs('storage', exist_ok=True)
    app.run(host='localhost', port=8000, debug=False)