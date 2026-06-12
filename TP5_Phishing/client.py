import requests
from getpass import getpass

API_URL = 'http://localhost:8000'
token = None
username = None

def login():
    global token, username
    print("\n=== AUTHENTIFICATION ===")
    user = input("Utilisateur (alice/bob): ")
    pwd = getpass("Mot de passe (password123): ")
    
    try:
        resp = requests.post(f"{API_URL}/auth/login", json={'username': user, 'password': pwd})
        
        if resp.status_code == 200:
            data = resp.json()
            token = data['token']
            username = data['username']
            print(f"✓ Connecté en tant que {username}")
            return True
        else:
            print(f"✗ {resp.json().get('error', 'Identifiants invalides')}")
            return False
    except Exception as e:
        print(f"✗ Erreur de connexion: {e}")
        return False

def submit_email():
    print("\n=== SOUMETTRE UN EMAIL ===")
    sender = input("Expéditeur: ")
    subject = input("Objet: ")
    print("Contenu (ligne vide pour terminer):")
    
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    
    content = "\n".join(lines)
    
    try:
        resp = requests.post(
            f"{API_URL}/submissions",
            json={'sender': sender, 'subject': subject, 'content': content},
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 201:
            data = resp.json()
            print(f"\n✓ Signalement #{data['id']} créé!")
            print(f"  Risque: {data['risk_level']} (score: {data['risk_score']})")
            print("  Raisons:")
            for reason in data['reasons']:
                print(f"    - {reason}")
        else:
            print(f"✗ {resp.json().get('error', 'Erreur inconnue')}")
    except Exception as e:
        print(f"✗ Erreur: {e}")

def list_submissions():
    print("\n=== SIGNALEMENTS ===")
    try:
        resp = requests.get(
            f"{API_URL}/submissions",
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if resp.status_code == 200:
            submissions = resp.json().get('submissions', [])
            if not submissions:
                print("Aucun signalement trouvé")
            else:
                for s in submissions:
                    print(f"[{s['id']}] {s['subject'][:50]} - {s['analysis']['risk_level']}")
        else:
            print(f"✗ {resp.json().get('error')}")
    except Exception as e:
        print(f"✗ Erreur: {e}")

def main():
    if not login():
        return
    
    while True:
        print("\n" + "="*50)
        print("1. Soumettre un email suspect")
        print("2. Voir mes signalements")
        print("3. Quitter")
        print("="*50)
        
        choice = input("Choix: ")
        
        if choice == '1':
            submit_email()
        elif choice == '2':
            list_submissions()
        elif choice == '3':
            print("Au revoir!")
            break
        else:
            print("Option invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == '__main__':
    print("\n🔒 PLATEFORME DE DÉTECTION PHISHING")
    main()