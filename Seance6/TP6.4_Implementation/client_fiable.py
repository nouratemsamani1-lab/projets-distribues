"""
TP6.4 - Client API avec Timeouts, Retry et Backoff
"""

import requests
import time
import random
import uuid
import json

class ResilientClient:
    """Client API résilient avec timeouts, retry et backoff exponentiel"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def request_with_retry(self, method, endpoint, max_retries=3, timeout=10, **kwargs):
        """
        Effectue une requête avec retry automatique
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.request(method, url, timeout=timeout, **kwargs)
                
                # Succès (2xx, 3xx)
                if response.status_code < 400:
                    if self.token and 'Authorization' not in kwargs.get('headers', {}):
                        print(f"✅ {method} {endpoint} - {response.status_code}")
                    return response
                
                # Rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 30))
                    print(f"⚠️ Rate limit. Attente {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                # Erreur 4xx (sauf 429) : ne pas retenter
                if 400 <= response.status_code < 500:
                    print(f"❌ Erreur client {response.status_code}: {response.text[:100]}")
                    return response
                
                # Erreur 5xx : retenter avec backoff
                if attempt < max_retries:
                    delay = random.uniform(0, min(1.0 * (2 ** attempt), 30))
                    print(f"🔄 Tentative {attempt+1}/{max_retries} échouée ({response.status_code}). Retry dans {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    print(f"💀 Échec après {max_retries} tentatives")
                    return response
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    delay = random.uniform(0, min(1.0 * (2 ** attempt), 30))
                    print(f"⏰ Timeout. Retry dans {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    delay = random.uniform(0, min(1.0 * (2 ** attempt), 30))
                    print(f"🔌 Erreur connexion. Retry dans {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise
        
        raise Exception(f"Échec après {max_retries} tentatives")
    
    def login(self, username, password):
        """Authentification"""
        print(f"\n🔐 Tentative de connexion: {username}")
        
        response = self.request_with_retry(
            'POST', '/auth/login',
            json={'username': username, 'password': password},
            max_retries=2,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['token']
            print(f"✅ Connecté en tant que {username} (rôle: {data['role']})")
            return True
        else:
            print(f"❌ Échec connexion: {response.json().get('message', 'Erreur')}")
            return False
    
    def create_document(self, title, content, tags=None):
        """Crée un document avec Idempotency-Key"""
        if not self.token:
            print("❌ Non authentifié")
            return None
        
        print(f"\n📝 Création du document: {title}")
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Idempotency-Key': str(uuid.uuid4()),
            'Content-Type': 'application/json'
        }
        
        data = {
            'title': title,
            'content': content,
            'tags': tags or []
        }
        
        response = self.request_with_retry(
            'POST', '/documents',
            headers=headers,
            json=data,
            max_retries=1,
            timeout=15
        )
        
        if response.status_code == 201:
            doc = response.json()
            print(f"✅ Document créé: {doc['id']}")
            return doc
        else:
            print(f"❌ Échec création: {response.json().get('message', 'Erreur')}")
            return None
    
    def get_documents(self, page=1, per_page=20):
        """Liste les documents"""
        if not self.token:
            print("❌ Non authentifié")
            return []
        
        print(f"\n📋 Récupération des documents (page {page})")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = self.request_with_retry(
            'GET', f'/documents?page={page}&per_page={per_page}',
            headers=headers,
            max_retries=2,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['pagination']['total']} documents trouvés")
            return data['data']
        else:
            print(f"❌ Échec: {response.json().get('message', 'Erreur')}")
            return []
    
    def get_document(self, doc_id):
        """Récupère un document par son ID"""
        if not self.token:
            print("❌ Non authentifié")
            return None
        
        print(f"\n🔍 Récupération du document: {doc_id}")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = self.request_with_retry(
            'GET', f'/documents/{doc_id}',
            headers=headers,
            max_retries=2,
            timeout=10
        )
        
        if response.status_code == 200:
            doc = response.json()
            print(f"✅ Document trouvé: {doc['title']}")
            return doc
        else:
            print(f"❌ {response.json().get('message', 'Non trouvé')}")
            return None
    
    def update_document(self, doc_id, title, content, tags=None):
        """Met à jour un document"""
        if not self.token:
            print("❌ Non authentifié")
            return None
        
        print(f"\n✏️ Mise à jour du document: {doc_id}")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        data = {
            'title': title,
            'content': content,
            'tags': tags or []
        }
        
        response = self.request_with_retry(
            'PUT', f'/documents/{doc_id}',
            headers=headers,
            json=data,
            max_retries=2,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Document mis à jour")
            return response.json()
        else:
            print(f"❌ {response.json().get('message', 'Erreur')}")
            return None
    
    def delete_document(self, doc_id):
        """Supprime un document"""
        if not self.token:
            print("❌ Non authentifié")
            return False
        
        print(f"\n🗑️ Suppression du document: {doc_id}")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = self.request_with_retry(
            'DELETE', f'/documents/{doc_id}',
            headers=headers,
            max_retries=2,
            timeout=8
        )
        
        if response.status_code == 204:
            print(f"✅ Document supprimé")
            return True
        else:
            print(f"❌ {response.json().get('message', 'Erreur') if response.text else 'Erreur'}")
            return False
    
    def search(self, query, page=1, per_page=20):
        """Recherche des documents"""
        if not self.token:
            print("❌ Non authentifié")
            return []
        
        print(f"\n🔎 Recherche: '{query}'")
        
        headers = {'Authorization': f'Bearer {self.token}'}
        
        response = self.request_with_retry(
            'GET', f'/search?q={query}&page={page}&per_page={per_page}',
            headers=headers,
            max_retries=2,
            timeout=8
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['total']} résultats trouvés")
            return data['results']
        else:
            print(f"❌ {response.json().get('message', 'Erreur')}")
            return []


def demo():
    """Démonstration du client"""
    print("="*60)
    print("🚀 DÉMONSTRATION - CLIENT API FIABLE")
    print("="*60)
    
    client = ResilientClient("http://localhost:5000")
    
    # 1. Login
    if not client.login("alice", "password123"):
        print("Impossible de continuer sans authentification")
        return
    
    # 2. Créer un document
    doc = client.create_document(
        title="Mon premier document",
        content="Ceci est le contenu de mon document de test.",
        tags=["test", "important"]
    )
    
    if not doc:
        # Essayer avec bob si alice échoue
        client.login("bob", "password123")
        doc = client.create_document(
            title="Document de bob",
            content="Contenu du document de bob",
            tags=["bob", "test"]
        )
    
    # 3. Lister les documents
    docs = client.get_documents()
    
    # 4. Chercher
    results = client.search("document")
    
    print("\n" + "="*60)
    print("✅ DÉMONSTRATION TERMINÉE")
    print("="*60)


if __name__ == "__main__":
    demo()