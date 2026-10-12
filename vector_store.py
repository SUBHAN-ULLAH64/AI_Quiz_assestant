"""Persistent Chroma vector store for course chunks."""
from pathlib import Path
import hashlib
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

ROOT = Path(__file__).resolve().parent
DB_DIR = ROOT / "data" / "chroma"
DB_DIR.mkdir(parents=True, exist_ok=True)

def get_collection():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    return client.get_or_create_collection(
        name="course_material",
        embedding_function=DefaultEmbeddingFunction(),
        metadata={"hnsw:space": "cosine"},
    )

def store_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0
    collection = get_collection()
    ids, docs, metas = [], [], []
    for item in chunks:
        identity = f"{item['source_file']}|{item['file_hash']}|{item['chunk_index']}"
        ids.append(hashlib.sha256(identity.encode()).hexdigest())
        docs.append(item["text"])
        metas.append({
            "source_file": item["source_file"],
            "file_hash": item["file_hash"],
            "source_location": item["source_location"],
            "section_index": int(item["section_index"]),
            "chunk_index": int(item["chunk_index"]),
        })
    collection.upsert(ids=ids, documents=docs, metadatas=metas)
    return len(ids)

def search_chunks(query: str, top_k: int = 5) -> list[dict]:
    query = query.strip()
    if not query:
        return []
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []
    result = collection.query(
        query_texts=[query],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )
    matches = []
    for i, doc in enumerate(result["documents"][0]):
        meta = result["metadatas"][0][i]
        matches.append({
            "id": result["ids"][0][i],
            "text": doc,
            "source_file": meta["source_file"],
            "source_location": meta["source_location"],
            "file_hash": meta["file_hash"],
            "chunk_index": int(meta["chunk_index"]),
            "distance": float(result["distances"][0][i]),
        })
    return matches

def get_database_stats() -> dict:
    collection = get_collection()
    return {"total_chunks": collection.count(), "collection_name": collection.name,
            "database_path": str(DB_DIR)}

def list_source_files() -> list[str]:
    collection = get_collection()
    if collection.count() == 0:
        return []
    result = collection.get(include=["metadatas"])
    return sorted({m["source_file"] for m in result["metadatas"] if m})
