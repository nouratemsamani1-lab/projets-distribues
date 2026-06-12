import requests

API_URL = 'http://localhost:8000'
token = None

def login():
    global token
    print("\n=== AUTHENTIFICATION ===")
    user = input("Utilisateur (alice): ")
    pwd = input("Mot de passe (password123): ")
    
    try:
        response = requests.post(f"{API_URL}/auth/login", json={"username": user, "password": pwd})
        
        if response.status_code == 200:
            data = response.json()
            token = data['token']
            print(f"\n✓ Connecté en tant que {data['username']} (rôle: {data['role']})")
            return True
        else:
            print(f"\n✗ Échec: {response.json().get('error', 'Erreur')}")
            return False
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        return False

def submit_email():
    global token
    print("\n=== NOUVEL EMAIL ===")
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
        response = requests.post(
            f"{API_URL}/submissions",
            json={"sender": sender, "subject": subject, "content": content},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"\n✓ Signalement #{data['id']}")
            print(f"  Risque: {data['risk_level']} (score: {data['risk_score']})")
            print("  Justification:")
            for r in data['reasons']:
                print(f"    - {r}")
        else:
            print(f"\n✗ {response.json().get('error', 'Erreur')}")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")

def list_submissions():
    global token
    print("\n=== SIGNALEMENTS ===")
    try:
        response = requests.get(f"{API_URL}/submissions", headers={"Authorization": f"Bearer {token}"})
        if response.status_code == 200:
            subs = response.json().get('submissions', [])
            if not subs:
                print("Aucun signalement")
            for s in subs:
                print(f"[{s['id']}] {s['subject'][:40]} - {s['analysis']['risk_level']}")
        else:
            print(f"✗ {response.json().get('error')}")
    except Exception as e:
        print(f"✗ Erreur: {e}")

def main():
    print("\n🔒 PLATEFORME PHISHING")
    if not login():
        return
    
    while True:
        print("\n1. Soumettre email")
        print("2. Voir signalements")
        print("3. Quitter")
        choice = input("Choix: ")
        
        if choice == '1':
            submit_email()
        elif choice == '2':
            list_submissions()
        elif choice == '3':
            break
        input("\nAppuyez sur Entrée...")

if __name__ == "__main__":
    main()