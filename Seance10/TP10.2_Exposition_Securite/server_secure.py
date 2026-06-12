"""
TP10.2 - DocumentService avec Politique d'Exposition et Sécurité
Ajout d'authentification par token et contrôle d'accès
"""

import Pyro5.api
import logging
import secrets
import hashlib
import hmac
from typing import List, Dict
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# Tokens valides (en production: stocker dans une base)
VALID_TOKENS = {
    "admin_token_2024": {"role": "admin", "user": "alice"},
    "user_token_2024": {"role": "user", "user": "bob"},
}

# Base de données simulée
_DOCUMENTS = {
    "doc_001": {
        "title": "Rapport annuel 2024",
        "content": "Contenu confidentiel...",
        "author": "Alice",
        "classification": "confidential"
    },
    "doc_002": {
        "title": "Guide utilisateur",
        "content": "Guide public...",
        "author": "Bob",
        "classification": "public"
    }
}

# ============================================================
# SERVICE SÉCURISÉ
# ============================================================

@Pyro5.api.expose
class SecureDocumentService:
    """
    Service de documents avec authentification et contrôle d'accès.
    """
    
    def _verify_token(self, token: str) -> Dict:
        """
        Vérifie la validité du token et retourne les informations.
        Méthode INTERNE - non exposée à distance.
        """
        if not isinstance(token, str):
            logger.warning(f"Token invalide: type {type(token)}")
            raise PermissionError("Authentification requise")
        
        if token not in VALID_TOKENS:
            logger.warning(f"Token invalide reçu: {token[:20]}...")
            raise PermissionError("Authentification requise")
        
        logger.info(f"Token valide pour: {VALID_TOKENS[token]['user']}")
        return VALID_TOKENS[token]
    
    def _check_access(self, token_info: Dict, required_role: str, doc_id: str = None):
        """
        Vérifie les droits d'accès.
        """
        if required_role == "admin" and token_info["role"] != "admin":
            logger.warning(f"Accès admin refusé pour {token_info['user']}")
            raise PermissionError("Permission insuffisante")
        
        # Vérification propriétaire pour les documents
        if doc_id and doc_id in _DOCUMENTS:
            if token_info["role"] != "admin":
                owner = _DOCUMENTS[doc_id].get("author")
                if owner and owner.lower() != token_info["user"]:
                    logger.warning(f"Accès non autorisé au document {doc_id} par {token_info['user']}")
                    raise PermissionError("Accès non autorisé")
        
        return True
    
    # ============================================================
    # MÉTHODES EXPOSÉES (avec authentification)
    # ============================================================
    
    def list_documents(self, token: str) -> List[str]:
        """
        Liste les documents accessibles.
        Nécessite authentification.
        """
        token_info = self._verify_token(token)
        logger.info(f"list_documents appelé par {token_info['user']}")
        
        # Admin voit tout, user voit seulement ses documents
        if token_info["role"] == "admin":
            return list(_DOCUMENTS.keys())
        else:
            return [
                doc_id for doc_id, doc in _DOCUMENTS.items()
                if doc.get("author", "").lower() == token_info["user"]
            ]
    
    def get_document_content(self, doc_id: str, token: str) -> str:
        """
        Récupère le contenu d'un document.
        Nécessite authentification + droits.
        """
        token_info = self._verify_token(token)
        self._check_access(token_info, "user", doc_id)
        
        if doc_id not in _DOCUMENTS:
            logger.warning(f"Document non trouvé: {doc_id}")
            raise KeyError("Document introuvable")
        
        logger.info(f"Document {doc_id} servi à {token_info['user']}")
        return _DOCUMENTS[doc_id]["content"]
    
    def create_document(self, doc_id: str, title: str, content: str, 
                        classification: str, token: str) -> Dict:
        """
        Crée un nouveau document.
        Nécessite authentification + rôle admin.
        """
        token_info = self._verify_token(token)
        self._check_access(token_info, "admin")
        
        # Validation des entrées
        if not isinstance(doc_id, str) or len(doc_id) < 3:
            raise ValueError("doc_id invalide (min 3 caractères)")
        
        if not isinstance(title, str) or len(title) < 1:
            raise ValueError("title invalide")
        
        if classification not in ["public", "internal", "confidential"]:
            raise ValueError("classification invalide")
        
        # Création
        _DOCUMENTS[doc_id] = {
            "title": title,
            "content": content,
            "author": token_info["user"],
            "classification": classification
        }
        
        logger.info(f"Document {doc_id} créé par {token_info['user']}")
        return {"status": "created", "doc_id": doc_id}
    
    def delete_document(self, doc_id: str, token: str) -> Dict:
        """
        Supprime un document.
        Nécessite authentification + rôle admin.
        """
        token_info = self._verify_token(token)
        self._check_access(token_info, "admin")
        
        if doc_id not in _DOCUMENTS:
            raise KeyError("Document introuvable")
        
        del _DOCUMENTS[doc_id]
        logger.warning(f"Document {doc_id} supprimé par {token_info['user']}")
        return {"status": "deleted", "doc_id": doc_id}
    
    def _internal_reset(self, token: str):
        """
        Méthode INTERNE - ne doit PAS être exposée.
        En production, cette méthode ne doit pas porter @expose.
        """
        # Cette méthode ne serait jamais exposée dans un vrai service
        pass


# ============================================================
# SERVEUR
# ============================================================

def main():
    """
    Démarre le serveur sécurisé.
    """
    print("="*60)
    print("🔐 SERVEUR DOCUMENT SERVICE SÉCURISÉ")
    print("="*60)
    
    with Pyro5.api.Daemon() as daemon:
        ns = Pyro5.api.locate_ns()
        uri = daemon.register(SecureDocumentService())
        ns.register("bank.documents.secure", uri)
        
        print(f"✅ Service sécurisé enregistré")
        print(f"   URI: {uri}")
        print(f"   Nom: bank.documents.secure")
        print("\n🔑 Tokens valides:")
        for token, info in VALID_TOKENS.items():
            print(f"   - {token} ({info['role']})")
        
        print("\n🚀 Serveur démarré - Ctrl+C pour arrêter")
        daemon.requestLoop()


if __name__ == "__main__":
    main()