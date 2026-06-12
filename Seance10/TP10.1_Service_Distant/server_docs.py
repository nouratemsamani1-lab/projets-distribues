"""
TP10.1 - Service Distant de Gestion de Documents
Serveur Pyro5 exposant un objet DocumentService
"""

import Pyro5.api
import logging
from typing import List

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# BASE DE DONNÉES SIMULÉE
# ============================================================

_DOCUMENTS = {
    "doc_001": {
        "title": "Rapport annuel 2024",
        "content": "Contenu confidentiel du rapport annuel...",
        "author": "Alice Dupont",
        "classification": "confidential"
    },
    "doc_002": {
        "title": "Politique de sécurité",
        "content": "Version 3.2 de la politique de sécurité...",
        "author": "Bob Martin",
        "classification": "internal"
    },
    "doc_003": {
        "title": "Guide utilisateur",
        "content": "Guide d'utilisation public...",
        "author": "Charlie Bernard",
        "classification": "public"
    },
    "doc_004": {
        "title": "Stratégie 2025",
        "content": "Plan stratégique pour 2025...",
        "author": "Diana Prince",
        "classification": "confidential"
    }
}

# ============================================================
# SERVICE ORIENTÉ OBJET DISTANT
# ============================================================

@Pyro5.api.expose
class DocumentService:
    """
    Service de gestion de documents exposé comme objet distant.
    Toutes les méthodes décorées @expose sont accessibles à distance.
    """
    
    def list_documents(self) -> List[str]:
        """
        Retourne la liste des IDs de documents disponibles.
        """
        logger.info(f"Appel list_documents() - {len(_DOCUMENTS)} documents")
        return list(_DOCUMENTS.keys())
    
    def get_document_content(self, doc_id: str) -> str:
        """
        Retourne le contenu d'un document par son ID.
        Lève KeyError si le document n'existe pas.
        """
        logger.info(f"Appel get_document_content({doc_id})")
        
        if doc_id not in _DOCUMENTS:
            logger.warning(f"Document non trouvé: {doc_id}")
            raise KeyError(f"Document '{doc_id}' non trouvé")
        
        logger.info(f"Document {doc_id} servi avec succès")
        return _DOCUMENTS[doc_id]["content"]
    
    def get_document_metadata(self, doc_id: str) -> dict:
        """
        Retourne les métadonnées d'un document.
        """
        logger.info(f"Appel get_document_metadata({doc_id})")
        
        if doc_id not in _DOCUMENTS:
            logger.warning(f"Document non trouvé: {doc_id}")
            raise KeyError(f"Document '{doc_id}' non trouvé")
        
        # Retourne une copie sans données sensibles
        metadata = _DOCUMENTS[doc_id].copy()
        return metadata
    
    def get_documents_by_classification(self, classification: str) -> List[str]:
        """
        Retourne les IDs des documents ayant une certaine classification.
        """
        logger.info(f"Appel get_documents_by_classification({classification})")
        
        allowed = ["public", "internal", "confidential", "secret"]
        if classification not in allowed:
            raise ValueError(f"Classification invalide. Autorise: {allowed}")
        
        result = [
            doc_id for doc_id, doc in _DOCUMENTS.items()
            if doc["classification"] == classification
        ]
        
        logger.info(f"Trouvé {len(result)} documents avec classification {classification}")
        return result
    
    def _internal_reload_index(self):
        """
        Méthode INTERNE - NON EXPOSÉE (pas de @expose)
        Cette méthode ne sera PAS accessible à distance.
        """
        logger.info("Rechargement interne de l'index (non exposé)")
        # Cette méthode ne doit JAMAIS être appelée à distance
        pass
    
    def _get_db_connection(self):
        """
        Méthure INTERNE - NON EXPOSÉE
        Accès à la base de données - très sensible
        """
        pass


# ============================================================
# SERVEUR PRINCIPAL
# ============================================================

def main():
    """
    Démarre le serveur d'objets distants.
    """
    print("="*60)
    print("🔧 DÉMARRAGE DU SERVEUR DOCUMENT SERVICE")
    print("="*60)
    
    # Créer le daemon (serveur réseau)
    with Pyro5.api.Daemon() as daemon:
        
        # Localiser le name server
        try:
            ns = Pyro5.api.locate_ns()
            print("✅ Name server localisé")
        except Exception as e:
            print(f"❌ Erreur: Name server non trouvé. Démarrez-le avec:")
            print("   python -m Pyro5.nameserver")
            print(f"   Erreur: {e}")
            return
        
        # Créer et enregistrer l'objet dans le daemon
        service = DocumentService()
        uri = daemon.register(service)
        print(f"✅ Objet DocumentService enregistré")
        print(f"   URI: {uri}")
        
        # Publier l'objet dans le name server sous un nom logique
        ns.register("bank.documents.service", uri)
        print(f"✅ Objet publié dans le name server sous le nom: bank.documents.service")
        
        print("\n" + "="*60)
        print("🚀 SERVEUR EN ATTENTE DE REQUÊTES...")
        print("   Appuyez sur Ctrl+C pour arrêter")
        print("="*60)
        
        # Boucle principale
        daemon.requestLoop()


if __name__ == "__main__":
    main()