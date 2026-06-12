"""
TP6.5 - Tests de sécurité de l'API
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"
TOKEN = None

def test_health():
    """Test 1: Health check"""
    print("\n" + "="*50)
    print("TEST 1: Health Check")
    print("="*50)
    
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Réponse: {r.json()}")
    assert r.status_code == 200
    print("✅ Health check OK")

def test_login_ok():
    """Test 2: Login correct"""
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
    else:
        print(f"❌ Échec: {r.json()}")
    
    assert r.status_code == 200

def test_login_wrong():
    """Test 3: Login incorrect"""
    print("\n" + "="*50)
    print("TEST 3: Login incorrect")
    print("="*50)
    
    r = requests.post(f"{BASE_URL}/auth/login", 
                     json={"username": "alice", "password": "wrongpassword"})
    print(f"Status: {r.status_code}")
    print(f"Message: {r.json().get('message', '')}")
    assert r.status_code == 401
    print("✅ Login incorrect rejeté")

def test_create_document():
    """Test 4: Création document"""
    print("\n" + "="*50)
    print("TEST 4: Création document")
    print("="*50)
    
    global TOKEN
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Idempotency-Key': 'test-key-123',
        'Content-Type': 'application/json'
    }
    
    data = {
        "title": "Document de test",
        "content": "Contenu du document de test",
        "tags": ["test"]
    }
    
    r = requests.post(f"{BASE_URL}/documents", headers=headers, json=data)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 201:
        doc = r.json()
        print(f"✅ Document créé: {doc['id']}")
        print(f"Titre: {doc['title']}")
        return doc['id']
    else:
        print(f"❌ Échec: {r.json()}")
        return None

def test_get_documents():
    """Test 5: Liste des documents"""
    print("\n" + "="*50)
    print("TEST 5: Liste des documents")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {TOKEN}'}
    r = requests.get(f"{BASE_URL}/documents", headers=headers)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"✅ {data['pagination']['total']} documents trouvés")
    else:
        print(f"❌ Échec: {r.json()}")
    
    assert r.status_code == 200

def test_search():
    """Test 6: Recherche"""
    print("\n" + "="*50)
    print("TEST 6: Recherche")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {TOKEN}'}
    r = requests.get(f"{BASE_URL}/search?q=test", headers=headers)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        print(f"✅ {r.json()['total']} résultats trouvés")
    else:
        print(f"❌ Échec: {r.json()}")
    
    assert r.status_code == 200

def test_protected_no_token():
    """Test 7: Accès sans token"""
    print("\n" + "="*50)
    print("TEST 7: Accès sans token")
    print("="*50)
    
    r = requests.get(f"{BASE_URL}/documents")
    print(f"Status: {r.status_code}")
    assert r.status_code == 401
    print("✅ Accès refusé (token manquant)")

def test_admin_with_bob():
    """Test 8: Bob tente accès admin"""
    print("\n" + "="*50)
    print("TEST 8: Bob tente accès admin")
    print("="*50)
    
    # Login avec bob
    r = requests.post(f"{BASE_URL}/auth/login", 
                     json={"username": "bob", "password": "password123"})
    bob_token = r.json()["token"]
    
    headers = {'Authorization': f'Bearer {bob_token}'}
    r = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"Status: {r.status_code}")
    assert r.status_code == 403
    print("✅ Accès admin refusé (bob n'est pas admin)")

def test_admin_with_alice():
    """Test 9: Alice accès admin"""
    print("\n" + "="*50)
    print("TEST 9: Alice accès admin")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {TOKEN}'}
    r = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        users = r.json()['users']
        print(f"✅ Utilisateurs: {list(users.keys())}")
    else:
        print(f"❌ Échec: {r.json()}")
    
    assert r.status_code == 200

def test_idempotency():
    """Test 10: Idempotency Key"""
    print("\n" + "="*50)
    print("TEST 10: Idempotency Key")
    print("="*50)
    
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Idempotency-Key': 'same-key-456',
        'Content-Type': 'application/json'
    }
    
    data = {"title": "Test idempotence", "content": "Contenu"}
    
    # Première requête
    r1 = requests.post(f"{BASE_URL}/documents", headers=headers, json=data)
    print(f"Première requête: {r1.status_code}")
    
    # Deuxième requête avec même clé
    r2 = requests.post(f"{BASE_URL}/documents", headers=headers, json=data)
    print(f"Deuxième requête (même clé): {r2.status_code}")
    
    # Vérifier que la deuxième a été rejetée ou a retourné le même résultat
    if r1.status_code == 201 and r2.status_code == 200:
        print("✅ Idempotency Key fonctionne")
    elif r1.status_code == 201 and r2.status_code == 409:
        print("✅ Idempotency Key fonctionne (409 Conflict)")
    else:
        print(f"⚠️ Résultat inattendu: r1={r1.status_code}, r2={r2.status_code}")

def test_logout():
    """Test 11: Logout"""
    print("\n" + "="*50)
    print("TEST 11: Logout")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {TOKEN}'}
    r = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    print(f"Status: {r.status_code}")
    assert r.status_code == 204
    print("✅ Logout OK")

def test_token_invalid_after_logout():
    """Test 12: Token invalide après logout"""
    print("\n" + "="*50)
    print("TEST 12: Token invalide après logout")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {TOKEN}'}
    r = requests.get(f"{BASE_URL}/documents", headers=headers)
    print(f"Status: {r.status_code}")
    assert r.status_code == 401
    print("✅ Token correctement révoqué")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("🧪 TESTS DE SÉCURITÉ DE L'API")
    print("="*60)
    print("⚠️ Assurez-vous que l'API tourne sur http://localhost:5000")
    print("="*60)
    
    try:
        test_health()
        test_login_ok()
        test_login_wrong()
        doc_id = test_create_document()
        test_get_documents()
        test_search()
        test_protected_no_token()
        test_admin_with_bob()
        test_admin_with_alice()
        test_idempotency()
        test_logout()
        test_token_invalid_after_logout()
        
        print("\n" + "="*60)
        print("🎉 TOUS LES TESTS ONT RÉUSSI !")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST ÉCHOUÉ: {e}")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("Vérifiez que l'API est lancée: python api_securisee.py")


if __name__ == "__main__":
    run_all_tests()