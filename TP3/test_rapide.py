import requests

BASE = "http://localhost:5000"

print("="*50)
print("🧪 TEST RAPIDE TP3")
print("="*50)

# 1. Health
print("\n1. Health check:")
r = requests.get(f"{BASE}/health")
print(f"   {r.json()}")

# 2. Login alice
print("\n2. Connexion alice:")
r = requests.post(f"{BASE}/auth/login", json={"username":"alice","password":"password123"})
alice_token = r.json().get("token")
print(f"   Status: {r.status_code}")
print(f"   Rôle: {r.json().get('role')}")

# 3. Zone protégée avec alice
print("\n3. Zone protégée (alice):")
r = requests.get(f"{BASE}/api/protected", headers={"Authorization": f"Bearer {alice_token}"})
print(f"   {r.json().get('message')}")

# 4. Admin avec alice
print("\n4. Admin users (alice):")
r = requests.get(f"{BASE}/admin/users", headers={"Authorization": f"Bearer {alice_token}"})
print(f"   Utilisateurs: {list(r.json().get('users', {}).keys())}")

# 5. Login bob
print("\n5. Connexion bob:")
r = requests.post(f"{BASE}/auth/login", json={"username":"bob","password":"password123"})
bob_token = r.json().get("token")
print(f"   Status: {r.status_code}")

# 6. Admin avec bob (devrait échouer)
print("\n6. Admin users (bob - devrait échouer):")
r = requests.get(f"{BASE}/admin/users", headers={"Authorization": f"Bearer {bob_token}"})
print(f"   Status: {r.status_code} (403 = accès refusé)")

# 7. Inscription
print("\n7. Inscription nouvel utilisateur:")
r = requests.post(f"{BASE}/auth/register", json={"username":"testuser","password":"test123","email":"test@test.com"})
print(f"   Status: {r.status_code}")
if r.status_code == 201:
    print(f"   Message: {r.json().get('message')}")

print("\n" + "="*50)
print("✅ TP3 terminé avec succès!")
print("="*50)