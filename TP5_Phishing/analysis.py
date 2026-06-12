from flask import Flask, request, jsonify
import re

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    
    score = 0
    reasons = []
    content = data.get('content', '').lower()
    
    # Mots suspects
    keywords = ['urgent', 'verify', 'password', 'click', 'suspended', 'immediate']
    for kw in keywords:
        if kw in content:
            score += 10
            reasons.append(f"Mot suspect: {kw}")
    
    # URLs
    if 'http://' in content or 'https://' in content:
        score += 15
        reasons.append("Contient des URLs")
    
    # Points d'exclamation
    if data.get('content', '').count('!') > 3:
        score += 10
        reasons.append("Trop d'exclamations")
    
    # Détermination du risque
    if score >= 60:
        risk = "ÉLEVÉ"
    elif score >= 30:
        risk = "MOYEN"
    else:
        risk = "FAIBLE"
    
    return jsonify({
        'risk_score': score,
        'risk_level': risk,
        'reasons': reasons
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🔍 Analysis Service sur http://localhost:8002")
    app.run(host='localhost', port=8002, debug=False)