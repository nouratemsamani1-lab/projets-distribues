from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)

SERVICES = {
    'auth': 'http://localhost:8001',
    'analysis': 'http://localhost:8002'
}

TIMEOUT = 5
SUBMISSIONS_FILE = 'storage/submissions.json'

def load_submissions():
    try:
        with open(SUBMISSIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_submissions(submissions):
    with open(SUBMISSIONS_FILE, 'w') as f:
        json.dump(submissions, f, indent=2)

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
            
            request.user = resp.json()
            return f(*args, **kwargs)
            
        except requests.Timeout:
            return jsonify({'error': 'Service authentification indisponible'}), 503
        except:
            return jsonify({'error': 'Erreur interne'}), 500
    
    return decorated

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        resp = requests.post(
            f"{SERVICES['auth']}/auth/login",
            json=request.json,
            timeout=TIMEOUT
        )
        return jsonify(resp.json()), resp.status_code
    except requests.Timeout:
        return jsonify({'error': 'Service authentification indisponible'}), 503
    except:
        return jsonify({'error': 'Erreur interne'}), 500

@app.route('/submissions', methods=['POST'])
@require_auth
def submit_email():
    data = request.json
    
    required = ['sender', 'subject', 'content']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'Champ manquant: {field}'}), 400
    
    try:
        # Appel au service d'analyse
        analysis_resp = requests.post(
            f"{SERVICES['analysis']}/analyze",
            json=data,
            timeout=TIMEOUT
        )
        
        if analysis_resp.status_code != 200:
            return jsonify({'error': 'Erreur analyse'}), 500
        
        analysis = analysis_resp.json()
        
        # Sauvegarde
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
        
        return jsonify({
            'id': submission['id'],
            'risk_level': analysis['risk_level'],
            'risk_score': analysis['risk_score'],
            'reasons': analysis['reasons']
        }), 201
        
    except requests.Timeout:
        return jsonify({'error': 'Service analyse indisponible'}), 503
    except Exception as e:
        return jsonify({'error': 'Erreur interne'}), 500

@app.route('/submissions', methods=['GET'])
@require_auth
def list_submissions():
    submissions = load_submissions()
    
    # Filtrer selon le rôle
    if request.user['role'] != 'admin':
        submissions = [s for s in submissions if s['submitted_by'] == request.user['username']]
    
    # Ne pas renvoyer le contenu complet
    for s in submissions:
        if 'content' in s:
            s['content_preview'] = s['content'][:100] + '...' if len(s['content']) > 100 else s['content']
            del s['content']
    
    return jsonify({'submissions': submissions[-50:]})

@app.route('/submissions/<int:submission_id>', methods=['GET'])
@require_auth
def get_submission(submission_id):
    submissions = load_submissions()
    submission = next((s for s in submissions if s['id'] == submission_id), None)
    
    if not submission:
        return jsonify({'error': 'Signalement non trouvé'}), 404
    
    # Vérification des droits
    if request.user['role'] != 'admin' and submission['submitted_by'] != request.user['username']:
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    return jsonify(submission)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'gateway': 'running'})

if __name__ == '__main__':
    os.makedirs('storage', exist_ok=True)
    print("🚪 API Gateway sur http://localhost:8000")
    app.run(host='localhost', port=8000, debug=False)