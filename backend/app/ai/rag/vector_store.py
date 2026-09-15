"""Persisted FAISS evidence store. Documents must be curated before use."""
from pathlib import Path
import json
import faiss
import numpy as np
from app.core.config import settings
from app.ai.rag.embeddings import embedding_provider
from app.ai.schemas.milestone3_schema import EvidenceSource

class FAISSEvidenceStore:
    def __init__(self):
        self.path = Path(settings.FAISS_INDEX_PATH)
        self.path.mkdir(parents=True, exist_ok=True)
        self.index_path, self.documents_path = self.path / "evidence.index", self.path / "evidence.json"
        self.index = faiss.read_index(str(self.index_path)) if self.index_path.exists() else faiss.IndexFlatIP(embedding_provider.dimension)
        self.documents: list[dict] = json.loads(self.documents_path.read_text(encoding="utf-8")) if self.documents_path.exists() else []
    def add_documents(self, documents: list[EvidenceSource]) -> None:
        """Add curated evidence; this method intentionally accepts no model-generated facts."""
        if not documents: return
        self.index.add(np.array([embedding_provider.embed(item.content) for item in documents]))
        self.documents.extend(item.model_dump() for item in documents)
        faiss.write_index(self.index, str(self.index_path))
        self.documents_path.write_text(json.dumps(self.documents), encoding="utf-8")
    def search(self, query: str, limit: int) -> list[EvidenceSource]:
        if self.index.ntotal == 0: return []
        distances, ids = self.index.search(np.array([embedding_provider.embed(query)]), min(limit, self.index.ntotal))
        results: list[EvidenceSource] = []
        
        stopwords = {
            "a", "an", "the", "in", "on", "of", "for", "and", "or", "to", "is", "are", "was", "were",
            "be", "been", "by", "with", "that", "this", "it", "as", "from", "at", "about", "against",
            "between", "into", "through", "during", "before", "after", "above", "below", "up", "down",
            "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
            "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
            "just", "should", "now", "would", "could", "may", "might", "must", "also", "using"
        }
        query_terms = {w.strip(".,!?;:\"'()[]{}").lower() for w in query.split() if len(w) > 2} - stopwords

        for dist, idx in zip(distances[0], ids[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc_data = self.documents[idx]
            doc_text = doc_data.get("content", "")
            doc_terms = {w.strip(".,!?;:\"'()[]{}").lower() for w in doc_text.split() if len(w) > 2} - stopwords
            overlap = len(query_terms & doc_terms)
            score = float(dist)

            # Strict relevance check: require minimum embedding similarity and domain term overlap
            if score >= 0.35 and overlap >= 2:
                results.append(EvidenceSource(**doc_data))

        return results

faiss_evidence_store = FAISSEvidenceStore()
