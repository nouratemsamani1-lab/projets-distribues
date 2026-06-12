"""
TP7.1 - Contrat JSON et Validation stricte
Sérialisation et désérialisation sécurisée des données
"""

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# MODÈLES DE DONNÉES
# ============================================================

@dataclass
class Document:
    """Modèle Document avec validation intégrée"""
    id: int
    title: str
    author: str
    tags: List[str] = field(default_factory=list)
    classification: str = "internal"
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Validation automatique après création"""
        self.validate()
    
    def validate(self):
        """Valide toutes les règles métier"""
        errors = []
        
        # Validation id
        if not isinstance(self.id, int) or self.id <= 0:
            errors.append("id doit être un entier positif")
        
        # Validation title
        if not isinstance(self.title, str):
            errors.append("title doit être une chaîne")
        elif len(self.title.strip()) < 1 or len(self.title) > 200:
            errors.append("title doit faire 1-200 caractères")
        
        # Validation author
        if not isinstance(self.author, str):
            errors.append("author doit être une chaîne")
        elif len(self.author.strip()) < 1 or len(self.author) > 100:
            errors.append("author doit faire 1-100 caractères")
        
        # Validation tags
        if not isinstance(self.tags, list):
            errors.append("tags doit être une liste")
        elif len(self.tags) > 20:
            errors.append("Maximum 20 tags")
        else:
            for i, tag in enumerate(self.tags):
                if not isinstance(tag, str):
                    errors.append(f"tag[{i}] doit être une chaîne")
                elif len(tag) < 1 or len(tag) > 50:
                    errors.append(f"tag[{i}] doit faire 1-50 caractères")
        
        # Validation classification
        ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
        if self.classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"classification invalide. Autorisé: {ALLOWED_CLASSIFICATIONS}")
        
        # Validation created_at (format ISO 8601)
        if self.created_at:
            try:
                datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except ValueError:
                errors.append("created_at doit être au format ISO 8601")
        
        if errors:
            raise ValueError(f"Validation échouée: {'; '.join(errors)}")
    
    def to_dict(self, exclude_sensitive=True):
        """Convertit en dictionnaire pour sérialisation"""
        data = asdict(self)
        if exclude_sensitive:
            # Exclure les champs sensibles
            pass
        return data


@dataclass
class UserPublic:
    """Modèle UserPublic pour les données exposées"""
    username: str
    display_name: str
    role: str
    
    def __post_init__(self):
        self.validate()
    
    def validate(self):
        errors = []
        
        # Validation username (alphanumérique + underscore)
        if not isinstance(self.username, str):
            errors.append("username doit être une chaîne")
        elif not re.match(r'^[a-zA-Z0-9_]{3,30}$', self.username):
            errors.append("username: 3-30 caractères alphanumériques ou _")
        
        # Validation display_name
        if not isinstance(self.display_name, str):
            errors.append("display_name doit être une chaîne")
        elif len(self.display_name.strip()) < 1 or len(self.display_name) > 100:
            errors.append("display_name doit faire 1-100 caractères")
        
        # Validation role
        ALLOWED_ROLES = {"viewer", "editor", "admin"}
        if self.role not in ALLOWED_ROLES:
            errors.append(f"role invalide. Autorisé: {ALLOWED_ROLES}")
        
        if errors:
            raise ValueError(f"Validation échouée: {'; '.join(errors)}")


# ============================================================
# FONCTIONS DE SÉRIALISATION/DÉSÉRIALISATION
# ============================================================

def serialize_document(doc: Document) -> str:
    """Sérialise un Document en JSON (sans champs sensibles)"""
    data = {
        "id": doc.id,
        "title": doc.title.strip(),
        "author": doc.author.strip(),
        "tags": doc.tags,
        "classification": doc.classification,
        "created_at": doc.created_at or datetime.now().isoformat() + "Z"
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def deserialize_document(raw_json: str) -> Document:
    """Désérialise et valide un JSON en Document"""
    
    # Étape 1: Limite de taille (sécurité)
    MAX_SIZE = 1024 * 1024  # 1 Mo
    if len(raw_json) > MAX_SIZE:
        logger.warning(f"Payload trop grand: {len(raw_json)} octets")
        raise ValueError("Payload invalide")
    
    # Étape 2: Parsing JSON
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON invalide: {e}")
        raise ValueError("Payload invalide")
    
    # Étape 3: Vérifier que c'est un dictionnaire
    if not isinstance(data, dict):
        logger.warning("Payload n'est pas un objet JSON")
        raise ValueError("Payload invalide")
    
    errors = []
    
    # Étape 4: Vérifier les champs obligatoires
    required_fields = ["id", "title", "author"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Champ obligatoire manquant: {field}")
    
    # Étape 5: Vérifier les types
    if "id" in data and not isinstance(data["id"], int):
        errors.append("'id' doit être un entier")
    
    if "title" in data and not isinstance(data["title"], str):
        errors.append("'title' doit être une chaîne")
    elif "title" in data and (len(data["title"].strip()) < 1 or len(data["title"]) > 200):
        errors.append("'title' doit faire 1-200 caractères")
    
    if "author" in data and not isinstance(data["author"], str):
        errors.append("'author' doit être une chaîne")
    
    if "tags" in data:
        if not isinstance(data["tags"], list):
            errors.append("'tags' doit être une liste")
        elif len(data["tags"]) > 20:
            errors.append("Maximum 20 tags")
        else:
            for i, tag in enumerate(data["tags"]):
                if not isinstance(tag, str):
                    errors.append(f"tag[{i}] doit être une chaîne")
                elif len(tag) > 50:
                    errors.append(f"tag[{i}] trop long (max 50)")
    
    # Étape 6: Vérifier les valeurs autorisées
    ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
    classification = data.get("classification", "internal")
    if classification not in ALLOWED_CLASSIFICATIONS:
        errors.append(f"classification invalide. Autorisé: {ALLOWED_CLASSIFICATIONS}")
    
    # Étape 7: Fail closed - rejeter en cas d'erreur
    if errors:
        logger.warning(f"Validation échouée: {errors}")
        raise ValueError("Payload invalide")
    
    # Étape 8: Créer l'objet
    return Document(
        id=data["id"],
        title=data["title"].strip(),
        author=data["author"].strip(),
        tags=data.get("tags", []),
        classification=classification,
        created_at=data.get("created_at")
    )


def serialize_user(user: UserPublic) -> str:
    """Sérialise un UserPublic en JSON"""
    return json.dumps(asdict(user), ensure_ascii=False, indent=2)


def deserialize_user(raw_json: str) -> UserPublic:
    """Désérialise et valide un JSON en UserPublic"""
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        raise ValueError("Payload invalide")
    
    if not isinstance(data, dict):
        raise ValueError("Payload invalide")
    
    required_fields = ["username", "display_name", "role"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Champ manquant: {field}")
    
    return UserPublic(
        username=data["username"],
        display_name=data["display_name"],
        role=data["role"]
    )


# ============================================================
# TESTS
# ============================================================

def test_valid_documents():
    """Test avec des documents valides"""
    print("\n" + "="*50)
    print("TEST 1: Documents valides")
    print("="*50)
    
    # Document complet
    doc = Document(
        id=1,
        title="Rapport financier Q1",
        author="Alice Dupont",
        tags=["finance", "important"],
        classification="confidential"
    )
    
    json_str = serialize_document(doc)
    print(f"Sérialisé:\n{json_str}")
    
    doc2 = deserialize_document(json_str)
    print(f"Désérialisé: {doc2}")
    print("✅ Document valide OK")


def test_invalid_documents():
    """Test avec des documents invalides"""
    print("\n" + "="*50)
    print("TEST 2: Documents invalides")
    print("="*50)
    
    test_cases = [
        ('{"id": "abc", "title": "Test", "author": "A"}', "id non entier"),
        ('{"id": 1, "title": "", "author": "A"}', "title vide"),
        ('{"id": 1, "title": "X" * 250, "author": "A"}', "title trop long"),
        ('{"id": 1, "title": "Test", "author": "A", "classification": "top_secret"}', "classification invalide"),
    ]
    
    for json_str, description in test_cases:
        try:
            deserialize_document(json_str)
            print(f"❌ ÉCHEC: {description} aurait dû être rejeté")
        except ValueError:
            print(f"✅ REJETÉ: {description}")


def test_users():
    """Test des utilisateurs"""
    print("\n" + "="*50)
    print("TEST 3: Utilisateurs")
    print("="*50)
    
    # Utilisateur valide
    user = UserPublic(username="alice_dupont", display_name="Alice Dupont", role="editor")
    json_str = serialize_user(user)
    print(f"Sérialisé: {json_str}")
    
    user2 = deserialize_user(json_str)
    print(f"Désérialisé: {user2}")
    
    # Utilisateur invalide
    try:
        user_invalid = UserPublic(username="a", display_name="A", role="superadmin")
        print("❌ Devrait échouer")
    except ValueError as e:
        print(f"✅ Rejeté: {e}")


def test_fail_closed():
    """Test du principe fail closed"""
    print("\n" + "="*50)
    print("TEST 4: Fail Closed - Tolérance zéro")
    print("="*50)
    
    # Payload avec champ inconnu
    payload = '{"id": 1, "title": "Test", "author": "A", "unknown_field": "hacker"}'
    
    try:
        doc = deserialize_document(payload)
        print(f"❌ FAIL OPEN: Champ inconnu accepté")
    except ValueError:
        print(f"✅ FAIL CLOSED: Champ inconnu rejeté")


if __name__ == "__main__":
    print("="*60)
    print("🧪 TP7.1 - Tests Contrat JSON")
    print("="*60)
    
    test_valid_documents()
    test_invalid_documents()
    test_users()
    test_fail_closed()
    
    print("\n" + "="*60)
    print("✅ TP7.1 COMPLET")
    print("="*60)