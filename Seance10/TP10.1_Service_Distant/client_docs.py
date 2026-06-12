"""
TP10.1 - Client du Service Distant de Gestion de Documents
Consomme l'objet DocumentService via Pyro5
"""

import Pyro5.api
import sys
import time


class DocumentClient:
    """
    Client pour le DocumentService distant.
    Gère la connexion et les appels distants.
    """
    
    def __init__(self, service_name="bank.documents.service"):
        self.service_name = service_name
        self.proxy = None
        self.connected = False
    
    def connect(self):
        """
        Se connecte au service distant via le name server.
        """
        try:
            # Localiser le name server
            ns = Pyro5.api.locate_ns()
            print(f"✅ Name server localisé")
            
            # Récupérer l'URI du service
            uri = ns.lookup(self.service_name)
            print(f"✅ Service '{self.service_name}' trouvé")
            print(f"   URI: {uri}")
            
            # Créer le proxy
            self.proxy = Pyro5.api.Proxy(uri)
            self.connected = True
            print(f"✅ Proxy créé - prêt à appeler les méthodes")
            return True
            
        except Pyro5.errors.NamingError:
            print(f"❌ Service '{self.service_name}' non trouvé dans le name server")
            print("   Vérifiez que le serveur est lancé")
            return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def list_documents(self):
        """
        Appelle la méthode list_documents() à distance.
        """
        if not self.connected:
            print("❌ Non connecté")
            return []
        
        try:
            # Timeout de 5 secondes
            result = self.proxy.list_documents(_pyroTimeout=5)
            return result
        except Pyro5.errors.TimeoutError:
            print("⏰ Timeout: le serveur ne répond pas")
            return []
        except Exception as e:
            print(f"❌ Erreur lors de l'appel: {e}")
            return []
    
    def get_document_content(self, doc_id):
        """
        Appelle get_document_content() à distance.
        """
        if not self.connected:
            print("❌ Non connecté")
            return None
        
        try:
            result = self.proxy.get_document_content(doc_id, _pyroTimeout=5)
            return result
        except Pyro5.errors.TimeoutError:
            print(f"⏰ Timeout: le serveur ne répond pas")
            return None
        except KeyError as e:
            print(f"❌ Document non trouvé: {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def get_document_metadata(self, doc_id):
        """
        Appelle get_document_metadata() à distance.
        """
        if not self.connected:
            print("❌ Non connecté")
            return None
        
        try:
            result = self.proxy.get_document_metadata(doc_id, _pyroTimeout=5)
            return result
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def get_documents_by_classification(self, classification):
        """
        Appelle get_documents_by_classification() à distance.
        """
        if not self.connected:
            print("❌ Non connecté")
            return []
        
        try:
            result = self.proxy.get_documents_by_classification(classification, _pyroTimeout=5)
            return result
        except ValueError as e:
            print(f"❌ Classification invalide: {e}")
            return []
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return []
    
    def disconnect(self):
        """
        Ferme la connexion.
        """
        if self.proxy:
            self.proxy._pyroRelease()
            self.connected = False
            print("✅ Déconnecté")


def main():
    """
    Démonstration du client.
    """
    print("="*60)
    print("📱 CLIENT DOCUMENT SERVICE")
    print("="*60)
    
    client = DocumentClient()
    
    if not client.connect():
        print("\n💡 Assurez-vous que:")
        print("   1. Le name server tourne: python -m Pyro5.nameserver")
        print("   2. Le serveur est lancé: python server_docs.py")
        return
    
    print("\n" + "="*60)
    print("📋 TEST DES MÉTHODES DISTANTES")
    print("="*60)
    
    # Test 1: Lister les documents
    print("\n1️⃣ Liste des documents:")
    docs = client.list_documents()
    for doc in docs:
        print(f"   - {doc}")
    
    # Test 2: Récupérer le contenu d'un document
    print("\n2️⃣ Contenu du document 'doc_001':")
    content = client.get_document_content("doc_001")
    if content:
        print(f"   {content[:100]}...")
    
    # Test 3: Récupérer les métadonnées
    print("\n3️⃣ Métadonnées de 'doc_001':")
    metadata = client.get_document_metadata("doc_001")
    if metadata:
        for key, value in metadata.items():
            print(f"   {key}: {value}")
    
    # Test 4: Document inexistant
    print("\n4️⃣ Test document inexistant 'doc_999':")
    content = client.get_document_content("doc_999")
    if content is None:
        print("   ✅ Erreur gérée correctement")
    
    # Test 5: Filtrer par classification
    print("\n5️⃣ Documents avec classification 'confidential':")
    confidential_docs = client.get_documents_by_classification("confidential")
    for doc in confidential_docs:
        print(f"   - {doc}")
    
    client.disconnect()
    
    print("\n" + "="*60)
    print("✅ FIN DE LA DÉMONSTRATION")
    print("="*60)


if __name__ == "__main__":
    main()