
from flask import Flask, render_template_string, request, jsonify
import requests
import json
import os

app = Flask(__name__)
API_GATEWAY = 'http://localhost:8000'

# Template HTML/CSS/JS intégré
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plateforme Anti-Phishing</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
        }
        
        .login-form, .dashboard {
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        
        button:hover {
            opacity: 0.9;
        }
        
        .risk-high {
            color: #dc3545;
            font-weight: bold;
        }
        
        .risk-medium {
            color: #ffc107;
            font-weight: bold;
        }
        
        .risk-low {
            color: #28a745;
            font-weight: bold;
        }
        
        .submission-card {
            background: #f8f9fa;
            border-left: 4px solid;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
        }
        
        .submission-card:hover {
            transform: translateX(5px);
            transition: 0.3s;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        
        .nav-buttons {
            margin-bottom: 20px;
        }
        
        .logout-btn {
            background: #dc3545;
            float: right;
        }
        
        .alert {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #f8f9fa;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ Plateforme de Détection de Phishing</h1>
            <p>Système distribué - Analyse heuristique d'emails suspects</p>
        </div>
        
        <div id="loginSection" class="login-form">
            <h2>Authentification</h2>
            <div id="loginMessage"></div>
            <div class="form-group">
                <label>Utilisateur:</label>
                <input type="text" id="username" placeholder="alice">
            </div>
            <div class="form-group">
                <label>Mot de passe:</label>
                <input type="password" id="password" placeholder="password123">
            </div>
            <button onclick="login()">Se connecter</button>
        </div>
        
        <div id="dashboardSection" style="display:none;">
            <div class="nav-buttons">
                <button onclick="showSubmitForm()">📧 Soumettre un email</button>
                <button onclick="showSubmissions()">📋 Voir les signalements</button>
                <button onclick="showStats()">📊 Statistiques</button>
                <button class="logout-btn" onclick="logout()">🚪 Déconnexion</button>
            </div>
            
            <div id="dashboardContent"></div>
        </div>
    </div>
    
    <script>
        let token = null;
        let userRole = null;
        
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('http://localhost:8000/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username, password})
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    token = data.token;
                    userRole = data.role;
                    document.getElementById('loginSection').style.display = 'none';
                    document.getElementById('dashboardSection').style.display = 'block';
                    showSubmitForm();
                } else {
                    document.getElementById('loginMessage').innerHTML = 
                        '<div class="alert alert-error">❌ ' + data.error + '</div>';
                }
            } catch (error) {
                document.getElementById('loginMessage').innerHTML = 
                    '<div class="alert alert-error">❌ Erreur de connexion</div>';
            }
        }
        
        async function showSubmitForm() {
            document.getElementById('dashboardContent').innerHTML = `
                <div class="login-form">
                    <h2>Soumettre un email suspect</h2>
                    <div class="form-group">
                        <label>Expéditeur:</label>
                        <input type="text" id="sender" placeholder="security@paypal.com">
                    </div>
                    <div class="form-group">
                        <label>Objet:</label>
                        <input type="text" id="subject" placeholder="URGENT: Compte suspendu">
                    </div>
                    <div class="form-group">
                        <label>Contenu:</label>
                        <textarea id="content" rows="6" placeholder="Contenu de l'email..."></textarea>
                    </div>
                    <button onclick="submitEmail()">Analyser</button>
                </div>
            `;
        }
        
        async function submitEmail() {
            const sender = document.getElementById('sender').value;
            const subject = document.getElementById('subject').value;
            const content = document.getElementById('content').value;
            
            try {
                const response = await fetch('http://localhost:8000/submissions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({sender, subject, content})
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    let riskClass = '';
                    if (data.risk_level === 'ÉLEVÉ') riskClass = 'risk-high';
                    else if (data.risk_level === 'MOYEN') riskClass = 'risk-medium';
                    else riskClass = 'risk-low';
                    
                    document.getElementById('dashboardContent').innerHTML = `
                        <div class="alert alert-success">
                            ✅ Signalement #${data.id} créé avec succès!
                            <br><br>
                            <strong>Score de risque:</strong> ${data.risk_score}/100<br>
                            <strong>Niveau:</strong> <span class="${riskClass}">${data.risk_level}</span><br>
                            <strong>Justification:</strong><br>
                            <ul>${data.reasons.map(r => `<li>${r}</li>`).join('')}</ul>
                        </div>
                        <button onclick="showSubmitForm()">Nouvel email</button>
                        <button onclick="showSubmissions()">Voir tous les signalements</button>
                    `;
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                alert('Erreur: ' + error);
            }
        }
        
        async function showSubmissions() {
            try {
                const response = await fetch('http://localhost:8000/submissions', {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    const submissions = data.submissions || [];
                    document.getElementById('dashboardContent').innerHTML = `
                        <div class="login-form">
                            <h2>📋 Historique des signalements (${submissions.length})</h2>
                            <table>
                                <thead>
                                    <tr><th>ID</th><th>Expéditeur</th><th>Objet</th><th>Score</th><th>Niveau</th><th>Date</th></tr>
                                </thead>
                                <tbody>
                                    ${submissions.map(s => `
                                        <tr>
                                            <td>${s.id}</td>
                                            <td>${s.sender}</td>
                                            <td>${s.subject.substring(0, 50)}</td>
                                            <td>${s.analysis.risk_score}</td>
                                            <td>${s.analysis.risk_level}</td>
                                            <td>${s.timestamp.substring(0, 19)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `;
                }
            } catch (error) {
                alert('Erreur: ' + error);
            }
        }
        
        async function showStats() {
            try {
                const response = await fetch('http://localhost:8000/submissions', {
                    headers: {'Authorization': `Bearer ${token}`}
                });
                
                const data = await response.json();
                const submissions = data.submissions || [];
                
                const high = submissions.filter(s => s.analysis.risk_level === 'ÉLEVÉ').length;
                const medium = submissions.filter(s => s.analysis.risk_level === 'MOYEN').length;
                const low = submissions.filter(s => s.analysis.risk_level === 'FAIBLE').length;
                
                document.getElementById('dashboardContent').innerHTML = `
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-number">${submissions.length}</div>
                            <div>Total signalements</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${high}</div>
                            <div>Risque ÉLEVÉ</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${medium}</div>
                            <div>Risque MOYEN</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${low}</div>
                            <div>Risque FAIBLE</div>
                        </div>
                    </div>
                    <div class="login-form">
                        <h3>Distribution des risques</h3>
                        <canvas id="riskChart" width="400" height="200"></canvas>
                    </div>
                `;
                
                // Ajouter un graphique simple
                const canvas = document.createElement('canvas');
                canvas.id = 'riskChart';
                document.getElementById('dashboardContent').appendChild(canvas);
            } catch (error) {
                alert('Erreur: ' + error);
            }
        }
        
        function logout() {
            token = null;
            document.getElementById('loginSection').style.display = 'block';
            document.getElementById('dashboardSection').style.display = 'none';
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        resp = requests.get(f'{API_GATEWAY}/submissions', 
                           headers={'Authorization': f'Bearer {token}'})
        return jsonify(resp.json()), resp.status_code
    except:
        return jsonify({'error': 'Service indisponible'}), 503

if __name__ == '__main__':
    print("="*50)
    print("🌐 Tableau de bord web démarré!")
    print("📱 Ouvrez votre navigateur sur: http://localhost:5000")
    print("="*50)
    app.run(host='localhost', port=5000, debug=False)
