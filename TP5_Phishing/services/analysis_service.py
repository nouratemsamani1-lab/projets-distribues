from flask import Flask, request, jsonify
import re
from urllib.parse import urlparse
import time

app = Flask(__name__)

# Règles heuristiques
SUSPICIOUS_KEYWORDS = [
    'urgent', 'immediate', 'verify', 'confirm', 'account', 'password',
    'click here', 'update', 'suspended', 'security alert', 'unusual activity',
    'congratulations', 'lottery', 'inheritance', 'bank', 'payment'
]

SUSPICIOUS_DOMAINS = [
    'bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly'
]

def extract_urls(text):
    """Extrait les URLs du texte"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)

def analyze_urls(urls):
    """Analyse les URLs suspectes"""
    score = 0
    reasons = []
    
    for url in urls:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # URL raccourcie
        if any(suspect in domain for suspect in SUSPICIOUS_DOMAINS):
            score += 20
            reasons.append(f"URL raccourcie détectée: {domain}")
        
        # IP à la place du domaine
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
            score += 30
            reasons.append(f"Adresse IP utilisée comme domaine: {domain}")
        
        # HTTPS manquant
        if parsed.scheme != 'https':
            score += 10
            reasons.append(f"URL sans HTTPS: {url[:50]}")
    
    return score, reasons

def analyze_content(content):
    """Analyse le contenu textuel"""
    score = 0
    reasons = []
    content_lower = content.lower()
    
    # Mots suspects
    found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in content_lower]
    if found_keywords:
        score += len(found_keywords) * 5
        reasons.append(f"Mots suspects: {', '.join(found_keywords[:5])}")
    
    # Urgence excessive (points d'exclamation, MAJ)
    exclamation_count = content.count('!')
    if exclamation_count > 3:
        score += 15
        reasons.append(f"Trop de points d'exclamation ({exclamation_count})")
    
    upper_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
    if upper_ratio > 0.3:
        score += 10
        reasons.append("Utilisation excessive de majuscules")
    
    # Demandes d'action
    action_phrases = ['click', 'download', 'open attachment', 'verify now', 'login']
    found_actions = [ap for ap in action_phrases if ap in content_lower]
    if found_actions:
        score += len(found_actions) * 8
        reasons.append(f"Demandes d'action: {', '.join(found_actions)}")
    
    return score, reasons

def check_spoofing(sender, content):
    """Détection d'usurpation d'identité simple"""
    score = 0
    reasons = []
    
    # Marques connues
    brands = ['paypal', 'amazon', 'microsoft', 'google', 'apple', 'bank']
    sender_lower = sender.lower()
    
    for brand in brands:
        if brand in sender_lower:
            # Vérification approximative
            if 'secure' in content.lower() or 'verify' in content.lower():
                score += 25
                reasons.append(f"Possible usurpation de {brand}")
                break
    
    return score, reasons

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    
    required_fields = ['sender', 'subject', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Champ manquant: {field}'}), 400
    
    # Limitation taille entrée
    if len(data.get('content', '')) > 50000:
        return jsonify({'error': 'Contenu trop long (max 50000 caractères)'}), 400
    
    total_score = 0
    all_reasons = []
    
    # Analyse du contenu
    content_score, content_reasons = analyze_content(data['content'])
    total_score += content_score
    all_reasons.extend(content_reasons)
    
    # Analyse des URLs
    urls = extract_urls(data['content'])
    if urls:
        url_score, url_reasons = analyze_urls(urls)
        total_score += url_score
        all_reasons.extend(url_reasons)
    
    # Détection usurpation
    spoof_score, spoof_reasons = check_spoofing(data['sender'], data['content'])
    total_score += spoof_score
    all_reasons.extend(spoof_reasons)
    
    # Objet suspect
    subject_lower = data['subject'].lower()
    if any(kw in subject_lower for kw in ['urgent', 'alert', 'verify', 'confirm']):
        total_score += 10
        all_reasons.append("Objet suspect")
    
    # Détermination du risque
    if total_score >= 60:
        risk = "ÉLEVÉ"
    elif total_score >= 30:
        risk = "MOYEN"
    else:
        risk = "FAIBLE"
    
    return jsonify({
        'risk_score': total_score,
        'risk_level': risk,
        'reasons': all_reasons[:10],  # Limite à 10 raisons
        'urls_found': urls[:5]  # Limite à 5 URLs
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='localhost', port=8002, debug=False)