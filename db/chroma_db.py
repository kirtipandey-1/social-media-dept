import chromadb
import uuid
from pathlib import Path

CHROMA_PATH = Path.home() / "social-media-dept" / "db" / "hooks"

def get_collection(path: str | None = None):
    p = path or str(CHROMA_PATH)
    Path(p).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=p)
    return client.get_or_create_collection(
        name="hooks",
        metadata={"hnsw:space": "cosine"}
    )

def upsert_hook(col, text: str, category: str = "general",
                source: str = "generated", engagement_score: float = 0.0,
                status: str = "testing") -> str:
    doc_id = str(uuid.uuid4())
    col.upsert(
        ids=[doc_id],
        documents=[text],
        metadatas=[{
            "category": category,
            "source": source,
            "engagement_score": engagement_score,
            "status": status,
        }]
    )
    return doc_id

def search_hooks(col, query: str, limit: int = 10,
                 category: str | None = None) -> list:
    if col.count() == 0:
        return []
    n = min(limit, col.count())
    kwargs = {"query_texts": [query], "n_results": n}
    if category:
        kwargs["where"] = {"category": category}
    results = col.query(**kwargs)
    out = []
    for i, doc in enumerate(results["documents"][0]):
        out.append({
            "id": results["ids"][0][i],
            "document": doc,
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return out
