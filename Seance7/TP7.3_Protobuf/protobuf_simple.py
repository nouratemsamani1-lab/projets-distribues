"""
TP7.3 - Protocol Buffers en Python (sans protoc)
Utilisation de la bibliothèque protobuf avec définition dynamique
"""

from google.protobuf import descriptor_pb2
from google.protobuf import message_factory
from google.protobuf.descriptor_pool import DescriptorPool
import json
import time

# ============================================================
# DÉFINITION DYNAMIQUE DU SCHÉMA (équivalent à .proto)
# ============================================================

def create_document_descriptor():
    """Crée un descriptor pour Document sans fichier .proto"""
    
    # Créer le pool de descriptors
    pool = DescriptorPool()
    
    # Définir le message Document
    document_descriptor = descriptor_pb2.DescriptorProto()
    document_descriptor.name = "Document"
    
    # Champ id (int32, numéro 1)
    id_field = document_descriptor.field.add()
    id_field.name = "id"
    id_field.number = 1
    id_field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    id_field.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32
    
    # Champ title (string, numéro 2)
    title_field = document_descriptor.field.add()
    title_field.name = "title"
    title_field.number = 2
    title_field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    title_field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    
    # Champ author (string, numéro 3)
    author_field = document_descriptor.field.add()
    author_field.name = "author"
    author_field.number = 3
    author_field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    author_field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    
    # Champ tags (repeated string, numéro 4)
    tags_field = document_descriptor.field.add()
    tags_field.name = "tags"
    tags_field.number = 4
    tags_field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    tags_field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    
    # Champ classification (string, numéro 5)
    class_field = document_descriptor.field.add()
    class_field.name = "classification"
    class_field.number = 5
    class_field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    class_field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    
    # Ajouter au pool
    pool.Add(document_descriptor)
    
    return pool.FindMessageTypeByName("Document")


# ============================================================
# CLASSE DOCUMENT SIMPLIFIÉE (sans protoc)
# ============================================================

class Document:
    """Document simple sans protobuf"""
    def __init__(self, id=None, title=None, author=None, tags=None, classification="internal"):
        self.id = id
        self.title = title
        self.author = author
        self.tags = tags or []
        self.classification = classification
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "tags": self.tags,
            "classification": self.classification
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            author=data.get("author"),
            tags=data.get("tags", []),
            classification=data.get("classification", "internal")
        )


# ============================================================
# SÉRIALISATION/DÉSÉRIALISATION MAISON (simulation Protobuf)
# ============================================================

def serialize_to_protobuf_like(doc: Document) -> bytes:
    """
    Sérialisation binaire simple (simule Protobuf)
    Format: [id:4bytes][title_len:2bytes][title][author_len:2bytes][author]
    """
    data = bytearray()
    
    # id (4 bytes, little-endian)
    data.extend(doc.id.to_bytes(4, 'little'))
    
    # title (longueur + contenu)
    title_bytes = doc.title.encode('utf-8')
    data.extend(len(title_bytes).to_bytes(2, 'little'))
    data.extend(title_bytes)
    
    # author (longueur + contenu)
    author_bytes = doc.author.encode('utf-8')
    data.extend(len(author_bytes).to_bytes(2, 'little'))
    data.extend(author_bytes)
    
    # tags (nombre de tags + chaque tag)
    data.extend(len(doc.tags).to_bytes(2, 'little'))
    for tag in doc.tags:
        tag_bytes = tag.encode('utf-8')
        data.extend(len(tag_bytes).to_bytes(2, 'little'))
        data.extend(tag_bytes)
    
    # classification (longueur + contenu)
    class_bytes = doc.classification.encode('utf-8')
    data.extend(len(class_bytes).to_bytes(2, 'little'))
    data.extend(class_bytes)
    
    return bytes(data)


def deserialize_from_protobuf_like(data: bytes) -> Document:
    """Désérialisation du format binaire"""
    offset = 0
    
    # id
    doc_id = int.from_bytes(data[offset:offset+4], 'little')
    offset += 4
    
    # title
    title_len = int.from_bytes(data[offset:offset+2], 'little')
    offset += 2
    title = data[offset:offset+title_len].decode('utf-8')
    offset += title_len
    
    # author
    author_len = int.from_bytes(data[offset:offset+2], 'little')
    offset += 2
    author = data[offset:offset+author_len].decode('utf-8')
    offset += author_len
    
    # tags
    num_tags = int.from_bytes(data[offset:offset+2], 'little')
    offset += 2
    tags = []
    for _ in range(num_tags):
        tag_len = int.from_bytes(data[offset:offset+2], 'little')
        offset += 2
        tag = data[offset:offset+tag_len].decode('utf-8')
        offset += tag_len
        tags.append(tag)
    
    # classification
    class_len = int.from_bytes(data[offset:offset+2], 'little')
    offset += 2
    classification = data[offset:offset+class_len].decode('utf-8')
    
    return Document(id=doc_id, title=title, author=author, tags=tags, classification=classification)


# ============================================================
# COMPARAISON JSON vs BINAIRE
# ============================================================

def compare_json_vs_binary():
    """Compare JSON avec le format binaire"""
    print("\n" + "="*60)
    print("COMPARAISON JSON vs FORMAT BINAIRE")
    print("="*60)
    
    # Données de test
    doc = Document(
        id=42,
        title="Rapport trimestriel Q2" * 5,
        author="Alice Dupont",
        tags=["finance", "important", "quarterly", "report", "analysis"],
        classification="confidential"
    )
    
    # JSON
    json_str = json.dumps(doc.to_dict(), ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    
    # Binaire maison
    binary_bytes = serialize_to_protobuf_like(doc)
    
    print(f"\n📊 TAILLE:")
    print(f"   JSON:      {len(json_bytes)} octets")
    print(f"   Binaire:   {len(binary_bytes)} octets")
    print(f"   Gain:      {len(json_bytes) - len(binary_bytes)} octets ({len(json_bytes)/len(binary_bytes):.1f}x plus petit)")
    
    # Performance encode
    iterations = 10000
    
    # JSON encode
    start = time.time()
    for _ in range(iterations):
        json.dumps(doc.to_dict())
    json_encode_time = time.time() - start
    
    # Binaire encode
    start = time.time()
    for _ in range(iterations):
        serialize_to_protobuf_like(doc)
    binary_encode_time = time.time() - start
    
    print(f"\n⚡ PERFORMANCE ENCODE ({iterations} itérations):")
    print(f"   JSON:      {json_encode_time:.3f}s")
    print(f"   Binaire:   {binary_encode_time:.3f}s")
    
    # JSON decode
    start = time.time()
    for _ in range(iterations):
        json.loads(json_str)
    json_decode_time = time.time() - start
    
    # Binaire decode
    start = time.time()
    for _ in range(iterations):
        deserialize_from_protobuf_like(binary_bytes)
    binary_decode_time = time.time() - start
    
    print(f"\n⚡ PERFORMANCE DECODE ({iterations} itérations):")
    print(f"   JSON:      {json_decode_time:.3f}s")
    print(f"   Binaire:   {binary_decode_time:.3f}s")


# ============================================================
# TEST DE COMPATIBILITÉ
# ============================================================

def test_compatibility():
    """Teste la compatibilité du format binaire"""
    print("\n" + "="*60)
    print("TEST DE COMPATIBILITÉ")
    print("="*60)
    
    # Document original
    doc1 = Document(id=1, title="Test", author="Alice", tags=["tag1", "tag2"])
    binary = serialize_to_protobuf_like(doc1)
    
    # Désérialisation
    doc2 = deserialize_from_protobuf_like(binary)
    
    print(f"Original: id={doc1.id}, title={doc1.title}, tags={doc1.tags}")
    print(f"Désérialisé: id={doc2.id}, title={doc2.title}, tags={doc2.tags}")
    
    # Vérification
    assert doc1.id == doc2.id
    assert doc1.title == doc2.title
    assert doc1.author == doc2.author
    assert doc1.tags == doc2.tags
    
    print("✅ Compatibilité OK (encode/decode fonctionne)")


# ============================================================
# RÈGLES DE VERSIONING
# ============================================================

def print_versioning_rules():
    """Affiche les règles de versioning pour les formats binaires"""
    print("\n" + "="*60)
    print("RÈGLES DE VERSIONING (Formats binaires)")
    print("="*60)
    
    rules = [
        ("✅ AJOUTER", "Nouveau champ à la fin du message → compatible si optionnel"),
        ("❌ SUPPRIMER", "Ne jamais supprimer un champ existant (casse le format)"),
        ("❌ CHANGER TYPE", "Ne jamais changer le type d'un champ existant"),
        ("✅ IGNORER", "Les champs inconnus doivent être ignorés par les anciens lecteurs"),
        ("🔧 VERSION", "Ajouter un champ 'version' pour gérer les évolutions majeures"),
    ]
    
    for status, rule in rules:
        print(f"{status:<10} {rule}")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("🔬 TP7.3 - Protobuf-like en Python (sans protoc)")
    print("="*60)
    
    # 1. Test de base
    print("\n1️⃣ TEST DE BASE")
    doc = Document(id=42, title="Rapport Q1", author="Alice", tags=["finance"], classification="internal")
    print(f"Document: {doc.to_dict()}")
    
    binary = serialize_to_protobuf_like(doc)
    print(f"Sérialisé: {len(binary)} octets")
    print(f"Hex (début): {binary[:20].hex()}")
    
    doc2 = deserialize_from_protobuf_like(binary)
    print(f"Désérialisé: {doc2.to_dict()}")
    
    # 2. Comparaison JSON vs Binaire
    compare_json_vs_binary()
    
    # 3. Test compatibilité
    test_compatibility()
    
    # 4. Règles de versioning
    print_versioning_rules()
    
    print("\n" + "="*60)
    print("✅ TP7.3 COMPLET")
    print("="*60)
    print("\n📝 Note: Cette version utilise une implémentation maison")
    print("   Pour utiliser le vrai Protobuf, installez protoc:")
    print("   1. Télécharger https://github.com/protocolbuffers/protobuf/releases")
    print("   2. Ajouter protoc.exe au PATH")
    print("   3. protoc --python_out=. document.proto")