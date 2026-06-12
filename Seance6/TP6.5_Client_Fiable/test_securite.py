"""
TP6.5 - Tests de sécurité de l'API
"""

import requests

BASE_URL = "http://localhost:5000"
TOKEN = None

def test_health():
    print("\n" + "="*50)
    print("TEST 1: Health Check")
    print("="*50)
    
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Réponse: {r.json()}")
    assert r.status_code == 200
    print("✅ Health check OK")

def test_login_ok():
    print("\n" + "="*50)
    print("TEST 2: Login correct")
    print("="*50)
    
    global TOKEN
    r = requests.post(f"{BASE_URL}/auth/login", 
                     json={"username": "alice", "password": "password123"})
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        TOKEN = r.json()["token"]
        print(f"✅ Token obtenu: {TOKEN[:30]}...")
        print(f"Rôle: {r.json()['role']}")
    
    assert r.status_code == 200

def test_login_wrong():
    print("\n" + "="*50)
    print("TEST 3: Login incorrect")
    print("="*50)
    
    r = requests.post(f"{BASE_URL}/auth/login", 
                     json={"username": "alice", "password": "wrong"})
    print(f"Status: {r.status_code}")
    assert r.status_code == 401
    print("✅ Login incorrect rejeté")

def test_create_document():
    print("\n" + "="*50)
    print("TEST 4: Création document")
    print("="*50)
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Idempotency-Key': 'test-key-123',
        'Content-Type': 'application/json'
    }
    
    data = {"title": "Test", "content": "Contenu", "tags": ["test"]}
    
    r = requests.post(f"{BASE_URL}/documents", headers=headers, json=data)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 201:
        print(f"✅ Document créé: {r.json()['id']}")
    else:
        print(f"❌ {r.json()}")
    
    assert r.status_code == 201

def test_protected_no_token():
    print("\n" + "="*50)
    print("TEST 5: Accès sans token")
    print("="*50)
    
    r = requests.get(f"{BASE_URL}/documents")
    print(f"Status: {r.status_code}")
    assert r.status_code == 401
    print("✅ Accès refusé")

def test_admin_with_bob():
    print("\n" + "="*50)
    print("TEST 6: Bob tente accès admin")
    print("="*50)
    
    r = requests.post(f"{BASE_URL}/auth/login", 
                     json={"username": "bob", "password": "password123"})
    bob_token = r.json()["token"]
    
    headers = {'Authorization': f'Bearer {bob_token}'}
    r = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"Status: {r.status_code}")
    assert r.status_code == 403
    print("✅ Accès admin refusé")

def test_admin_with_alice():
    print("\n" + "="*50)
    print("TEST 7: Alice accès admin")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {TOKEN}'}
    r = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        print(f"✅ Utilisateurs: {list(r.json()['users'].keys())}")
    
    assert r.status_code == 200

def run_all_tests():
    print("\n" + "="*60)
    print("🧪 TESTS DE SÉCURITÉ DE L'API")
    print("="*60)
    print("⚠️ Assurez-vous que l'API tourne sur http://localhost:5000")
    print("="*60)
    
    try:
        test_health()
        test_login_ok()
        test_login_wrong()
        test_create_document()
        test_protected_no_token()
        test_admin_with_bob()
        test_admin_with_alice()
        
        print("\n" + "="*60)
        print("🎉 TOUS LES TESTS ONT RÉUSSI !")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("Vérifiez que l'API est lancée: python api_securisee.py")

if __name__ == "__main__":
    run_all_tests()