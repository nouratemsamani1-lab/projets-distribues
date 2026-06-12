"""
TP7.2 - Versioning JSON (Compatibilité v1 → v2)
Gestion de l'évolution des contrats de données
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional

# ============================================================
# VERSION 1 : Modèle Document (ancien)
# ============================================================

@dataclass
class DocumentV1:
    """Version 1 du contrat - champs minimum"""
    id: int
    title: str
    author: str
    
    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "title": self.title,
            "author": self.author
        }, ensure_ascii=False)


# ============================================================
# VERSION 2 : Modèle Document (évolué)
# ============================================================

@dataclass
class DocumentV2:
    """Version 2 du contrat - ajout de champs optionnels"""
    id: int
    title: str
    author: str
    tags: List[str] = field(default_factory=list)
    classification: str = "internal"
    
    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "tags": self.tags,
            "classification": self.classification
        }, ensure_ascii=False)


# ============================================================
# DÉSÉRIALISEUR COMPATIBLE v1/v2
# ============================================================

def deserialize_document_v2_compatible(raw_json: str) -> DocumentV2:
    """
    Désérialise un document, compatible avec les payloads v1 et v2
    Stratégie: Champs manquants → valeurs par défaut
    """
    data = json.loads(raw_json)
    
    # Valeurs par défaut pour les champs v2
    tags = data.get("tags", [])
    classification = data.get("classification", "internal")
    
    # Validation des champs v1 (obligatoires)
    if "id" not in data or "title" not in data or "author" not in data:
        raise ValueError("Champs obligatoires v1 manquants")
    
    # Validation des types
    if not isinstance(data["id"], int):
        raise ValueError("id doit être un entier")
    if not isinstance(data["title"], str):
        raise ValueError("title doit être une chaîne")
    if not isinstance(data["author"], str):
        raise ValueError("author doit être une chaîne")
    
    # Validation des champs v2 s'ils sont présents
    if "tags" in data and not isinstance(data["tags"], list):
        raise ValueError("tags doit être une liste")
    if "classification" in data:
        ALLOWED = {"public", "internal", "confidential", "secret"}
        if data["classification"] not in ALLOWED:
            raise ValueError(f"classification invalide: {data['classification']}")
    
    return DocumentV2(
        id=data["id"],
        title=data["title"],
        author=data["author"],
        tags=tags,
        classification=classification
    )


# ============================================================
# MATRICE DE COMPATIBILITÉ
# ============================================================

def test_compatibility_matrix():
    """Teste toutes les combinaisons de compatibilité"""
    print("\n" + "="*60)
    print("MATRICE DE COMPATIBILITÉ")
    print("="*60)
    
    # Payload v1
    payload_v1 = '{"id": 1, "title": "Rapport v1", "author": "Alice"}'
    
    # Payload v2
    payload_v2 = '{"id": 2, "title": "Rapport v2", "author": "Bob", "tags": ["test"], "classification": "public"}'
    
    # Payload v2 avec classification invalide
    payload_v2_invalid = '{"id": 3, "title": "Test", "author": "Charlie", "classification": "top_secret"}'
    
    # Payload avec champ inconnu
    payload_unknown = '{"id": 4, "title": "Test", "author": "David", "priority": "high"}'
    
    results = []
    
    # Test 1: Lecteur v2 lit payload v1
    try:
        doc = deserialize_document_v2_compatible(payload_v1)
        results.append(("v1 → v2", "✅ Accepté", f"tags={doc.tags} (défaut), classification={doc.classification} (défaut)"))
    except Exception as e:
        results.append(("v1 → v2", "❌ Rejeté", str(e)))
    
    # Test 2: Lecteur v1 lit payload v2 (simulé)
    try:
        data = json.loads(payload_v2)
        doc_v1 = DocumentV1(id=data["id"], title=data["title"], author=data["author"])
        results.append(("v2 → v1 (lecture)", "✅ Accepté (ignore tags/classification)", f"Seuls id,title,author lus"))
    except Exception as e:
        results.append(("v2 → v1 (lecture)", "❌ Rejeté", str(e)))
    
    # Test 3: Payload v2 avec classification invalide
    try:
        doc = deserialize_document_v2_compatible(payload_v2_invalid)
        results.append(("v2 (classification invalide)", "❌ Rejeté (normal)", "Devrait être rejeté"))
    except ValueError:
        results.append(("v2 (classification invalide)", "✅ Rejeté", "Classification hors allowlist"))
    
    # Test 4: Payload avec champ inconnu
    try:
        doc = deserialize_document_v2_compatible(payload_unknown)
        results.append(("v2 + champ inconnu", "✅ Accepté (toléré)", f"Champ inconnu ignoré, doc={doc.id}"))
    except Exception as e:
        results.append(("v2 + champ inconnu", "❌ Rejeté", str(e)))
    
    # Afficher la matrice
    print("\n{:<25} {:<15} {:<30}".format("Cas", "Résultat", "Détail"))
    print("-" * 70)
    for cas, resultat, detail in results:
        print("{:<25} {:<15} {:<30}".format(cas, resultat, detail[:30]))


# ============================================================
# POLITIQUE DE VERSIONING
# ============================================================

def print_versioning_policy():
    """Affiche la politique de versioning recommandée"""
    print("\n" + "="*60)
    print("POLITIQUE DE VERSIONING JSON")
    print("="*60)
    
    rules = [
        ("✅ AJOUTER", "Nouveaux champs optionnels avec valeurs par défaut → compatible"),
        ("❌ SUPPRIMER", "Ne jamais supprimer un champ existant (cassant pour les anciens clients)"),
        ("❌ RENOMMER", "Renommer un champ = le supprimer + en ajouter un nouveau → cassant"),
        ("❌ CHANGER TYPE", "Changer le type d'un champ existant (ex: string→int) → cassure silencieuse"),
        ("✅ IGNORER", "Les champs inconnus doivent être ignorés (pas d'erreur)"),
        ("✅ DÉFAUTS", "Tout nouveau champ doit avoir une valeur par défaut logique"),
        ("✅ DOCUMENTER", "Toute évolution doit être documentée dans le contrat d'API"),
    ]
    
    for status, rule in rules:
        print(f"{status:<10} {rule}")


# ============================================================
# SIMULATION D'ÉVOLUTION API
# ============================================================

def simulate_api_evolution():
    """Simule l'évolution d'une API de v1 à v2"""
    print("\n" + "="*60)
    print("SIMULATION D'ÉVOLUTION API v1 → v2")
    print("="*60)
    
    # Ancien client envoie payload v1
    old_payload = '{"id": 100, "title": "Ancien document", "author": "Legacy"}'
    
    print("\n📨 Ancien client (v1) envoie:", old_payload)
    
    # Nouveau serveur (v2) reçoit et traite
    doc = deserialize_document_v2_compatible(old_payload)
    print(f"🖥️ Nouveau serveur (v2) reçoit: Document #{doc.id}")
    print(f"   - tags: {doc.tags} (valeur par défaut)")
    print(f"   - classification: {doc.classification} (valeur par défaut)")
    print("✅ Compatibilité ascendante OK")
    
    # Nouveau client envoie payload v2
    new_payload = '{"id": 200, "title": "Nouveau document", "author": "Modern", "tags": ["innovation"], "classification": "public"}'
    
    print("\n📨 Nouveau client (v2) envoie:", new_payload)
    
    # Ancien serveur (v1) lit
    data = json.loads(new_payload)
    doc_v1 = DocumentV1(id=data["id"], title=data["title"], author=data["author"])
    print(f"🖥️ Ancien serveur (v1) reçoit: Document #{doc_v1.id}")
    print("   (ignore tags et classification)")
    print("✅ Compatibilité descendante OK")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("📦 TP7.2 - Versioning JSON (v1 → v2)")
    print("="*60)
    
    test_compatibility_matrix()
    print_versioning_policy()
    simulate_api_evolution()
    
    print("\n" + "="*60)
    print("✅ TP7.2 COMPLET")
    print("="*60)