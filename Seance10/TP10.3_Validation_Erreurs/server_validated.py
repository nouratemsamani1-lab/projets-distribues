"""
TP10.3 - Service avec Validation Stricte et Erreurs Sûres
Implémentation des bonnes pratiques de validation et gestion d'erreurs
"""

import Pyro5.api
import logging
import re
from typing import List, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# VALIDATION DES ENTRÉES
# ============================================================

class InputValidator:
    """Validateur strict des entrées."""
    
    @staticmethod
    def validate_doc_id(doc_id: any) -> str:
        """
        Valide un identifiant de document.
        Règles:
        - Type: str
        - Longueur: 3-32 caractères
        - Format: alphanumérique + underscore
        """
        # Validation type
        if not isinstance(doc_id, str):
            logger.warning(f"Type invalide pour doc_id: {type(doc_id)}")
            raise ValueError("Identifiant invalide")
        
        # Validation longueur
        if len(doc_id) < 3 or len(doc_id) > 32:
            logger.warning(f"Longueur invalide pour doc_id: {len(doc_id)}")
            raise ValueError("Identifiant invalide")
        
        # Validation format (alphanumérique + underscore)
        if not re.match(r'^[a-zA-Z0-9_]+$', doc_id):
            logger.warning(f"Format invalide pour doc_id: {doc_id}")
            raise ValueError("Identifiant invalide")
        
        # Pas de caractères dangereux
        dangerous = ['..', '/', '\\', ';', '--', '\x00']
        for d in dangerous:
            if d in doc_id:
                logger.warning(f"Caractères dangereux dans doc_id: {doc_id}")
                raise ValueError("Identifiant invalide")
        
        return doc_id
    
    @staticmethod
    def validate_title(title: any) -> str:
        """Valide un titre."""
        if not isinstance(title, str):
            raise ValueError("Titre invalide")
        
        title = title.strip()
        if len(title) < 1 or len(title) > 200:
            raise ValueError("Titre doit faire 1-200 caractères")
        
        return title
    
    @staticmethod
    def validate_classification(classification: any) -> str:
        """Valide une classification."""
        allowed = ["public", "internal", "confidential", "secret"]
        
        if not isinstance(classification, str):
            raise ValueError("Classification invalide")
        
        if classification not in allowed:
            raise ValueError(f"Classification invalide. Autorisé: {allowed}")
        
        return classification
    
    @staticmethod
    def validate_token(token: any) -> str:
        """Valide un token d'authentification."""
        if not isinstance(token, str):
            raise ValueError("Authentification requise")
        
        if len(token) < 10 or len(token) > 100:
            raise ValueError("Authentification requise")
        
        return token


# ============================================================
# SERVICE AVEC VALIDATION
# ============================================================

# Tokens valides
VALID_TOKENS = {
    "secure_token_2024_admin": {"role": "admin", "user": "alice"},
    "secure_token_2024_user": {"role": "user", "user": "bob"},
}

# Base de données
_DOCUMENTS = {
    "doc_001": {
        "title": "Rapport financier",
        "content": "Contenu financier confidentiel...",
        "author": "alice",
        "classification": "confidential",
        "created_at": "2024-01-15"
    },
    "doc_002": {
        "title": "Guide technique",
        "content": "Documentation technique...",
        "author": "bob",
        "classification": "internal",
        "created_at": "2024-02-20"
    },
    "doc_003": {
        "title": "Document public",
        "content": "Informations publiques...",
        "author": "alice",
        "classification": "public",
        "created_at": "2024-03-10"
    }
}


@Pyro5.api.expose
class ValidatedDocumentService:
    """
    Service de documents avec validation stricte et erreurs sûres.
    """
    
    def _verify_token(self, token: str) -> dict:
        """
        Vérifie le token et retourne les infos utilisateur.
        """
        token = InputValidator.validate_token(token)
        
        if token not in VALID_TOKENS:
            logger.warning(f"Token invalide: {token[:20]}...")
            raise PermissionError("Authentification requise")
        
        return VALID_TOKENS[token]
    
    def _safe_error_response(self, error_msg: str, client_msg: str):
        """
        Journalise l'erreur détaillée en interne,
        retourne un message générique au client.
        """
        logger.error(f"Erreur interne: {error_msg}")
        raise ValueError(client_msg)
    
    # ============================================================
    # MÉTHODES EXPOSÉES
    # ============================================================
    
    def list_documents(self, token: str) -> List[str]:
        """
        Liste les documents accessibles.
        """
        try:
            token_info = self._verify_token(token)
            logger.info(f"list_documents par {token_info['user']}")
            
            if token_info["role"] == "admin":
                return list(_DOCUMENTS.keys())
            else:
                return [
                    doc_id for doc_id, doc in _DOCUMENTS.items()
                    if doc["author"] == token_info["user"]
                ]
        
        except PermissionError:
            raise  # Propager l'exception (message déjà générique)
        except Exception as e:
            self._safe_error_response(str(e), "Erreur de service")
    
    def get_document_content(self, doc_id: str, token: str) -> str:
        """
        Récupère le contenu d'un document avec validation stricte.
        """
        try:
            # 1. Validation du token
            token_info = self._verify_token(token)
            
            # 2. Validation du doc_id
            doc_id = InputValidator.validate_doc_id(doc_id)
            
            # 3. Vérification existence
            if doc_id not in _DOCUMENTS:
                logger.warning(f"Document non trouvé: {doc_id} par {token_info['user']}")
                raise KeyError("Document introuvable")
            
            # 4. Vérification droits (propriétaire ou admin)
            doc = _DOCUMENTS[doc_id]
            if doc["author"] != token_info["user"] and token_info["role"] != "admin":
                logger.warning(f"Accès refusé au document {doc_id} par {token_info['user']}")
                raise PermissionError("Accès non autorisé")
            
            # 5. Retour du contenu
            logger.info(f"Document {doc_id} servi à {token_info['user']}")
            return doc["content"]
        
        except (ValueError, KeyError, PermissionError):
            raise  # Propager les exceptions (messages déjà génériques)
        except Exception as e:
            self._safe_error_response(str(e), "Erreur de service")
    
    def create_document(self, doc_id: str, title: str, content: str,
                        classification: str, token: str) -> Dict:
        """
        Crée un nouveau document avec validation.
        """
        try:
            # 1. Validation token + droits admin
            token_info = self._verify_token(token)
            if token_info["role"] != "admin":
                logger.warning(f"Tentative de création par non-admin: {token_info['user']}")
                raise PermissionError("Permission insuffisante")
            
            # 2. Validation des entrées
            doc_id = InputValidator.validate_doc_id(doc_id)
            title = InputValidator.validate_title(title)
            classification = InputValidator.validate_classification(classification)
            
            # 3. Vérifier si doc existe déjà
            if doc_id in _DOCUMENTS:
                logger.warning(f"Document déjà existant: {doc_id}")
                raise ValueError("Document déjà existant")
            
            # 4. Création
            _DOCUMENTS[doc_id] = {
                "title": title,
                "content": content,
                "author": token_info["user"],
                "classification": classification,
                "created_at": "2024-06-13"
            }
            
            logger.info(f"Document {doc_id} créé par {token_info['user']}")
            return {"status": "created", "doc_id": doc_id}
        
        except (ValueError, KeyError, PermissionError):
            raise
        except Exception as e:
            self._safe_error_response(str(e), "Erreur de service")
    
    def search_documents(self, query: str, token: str) -> List[Dict]:
        """
        Recherche des documents par mot-clé.
        """
        try:
            token_info = self._verify_token(token)
            
            if not isinstance(query, str) or len(query) < 2:
                raise ValueError("Requête invalide")
            
            results = []
            for doc_id, doc in _DOCUMENTS.items():
                # Vérifier droits d'accès
                if doc["author"] != token_info["user"] and token_info["role"] != "admin":
                    continue
                
                # Recherche dans titre et contenu
                if query.lower() in doc["title"].lower() or query.lower() in doc["content"].lower():
                    results.append({
                        "id": doc_id,
                        "title": doc["title"],
                        "classification": doc["classification"]
                    })
            
            logger.info(f"Recherche '{query}' par {token_info['user']}: {len(results)} résultats")
            return results
        
        except ValueError:
            raise
        except Exception as e:
            self._safe_error_response(str(e), "Erreur de service")


# ============================================================
# SERVEUR
# ============================================================

def main():
    print("="*60)
    print("✅ SERVEUR AVEC VALIDATION STRICTE")
    print("="*60)
    
    with Pyro5.api.Daemon() as daemon:
        ns = Pyro5.api.locate_ns()
        uri = daemon.register(ValidatedDocumentService())
        ns.register("bank.documents.validated", uri)
        
        print(f"✅ Service enregistré sous: bank.documents.validated")
        print("\n🔑 Tokens de test:")
        print("   - secure_token_2024_admin (admin)")
        print("   - secure_token_2024_user (user)")
        print("\n🚀 Serveur démarré")
        daemon.requestLoop()


if __name__ == "__main__":
    main()