from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from build_index import MODEL_NAME, load_index

# Module-level singletons -- loaded once per process, reused on every call.
# In Streamlit this means one load per worker, not one load per interaction.
_model: SentenceTransformer | None = None
_embeddings: np.ndarray | None = None
_metadata: list[dict] | None = None


def _ensure_loaded() -> None:
    global _model, _embeddings, _metadata
    if _embeddings is None:
        _embeddings, _metadata = load_index()
    if _model is None:
        print(f"[retriever] Loading model '{MODEL_NAME}' ...")
        _model = SentenceTransformer(MODEL_NAME)
        print("[retriever] Model ready.")


def retrieve(query_text: str, top_k: int = 3) -> list[dict]:
    """Return the top_k most relevant FAQ entries for query_text.

    Each result dict contains all stored metadata fields plus:
        score  float  cosine similarity in [0, 1] -- higher is better.
    """
    if not query_text or not query_text.strip():
        return []

    _ensure_loaded()

    query_vec: np.ndarray = _model.encode(
        query_text.strip(),
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    # cosine similarity == dot product because embeddings are unit-length
    scores: np.ndarray = _embeddings @ query_vec

    n = min(top_k, len(_metadata))
    top_indices = np.argsort(scores)[::-1][:n]

    results: list[dict] = []
    for idx in top_indices:
        entry = dict(_metadata[idx])
        entry["score"] = float(scores[idx])
        results.append(entry)

    return results


def retrieve_for_species(
    query_text: str,
    species: str,
    top_k: int = 3,
) -> list[dict]:
    """Like retrieve(), but post-filters to a specific species ('dog' or 'cat').

    Fetches 3*top_k candidates first so filtering does not starve the result set.
    """
    candidates = retrieve(query_text, top_k=top_k * 3)
    species_lower = species.lower()
    filtered = [r for r in candidates if species_lower in r.get("species", [])]
    return filtered[:top_k]


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "my dog vomited twice today"
    print(f"\nQuery: {query!r}\n{'=' * 60}")

    hits = retrieve(query, top_k=3)
    if not hits:
        print("No results -- run  python build_index.py  first.")
        sys.exit(1)

    URGENCY_ICON = {
        "emergency": "[EMERGENCY]",
        "urgent":    "[URGENT]",
        "monitor":   "[MONITOR]",
        "routine":   "[ROUTINE]",
    }

    for rank, r in enumerate(hits, start=1):
        icon = URGENCY_ICON.get(r["urgency"], "")
        print(f"\n#{rank}  score={r['score']:.3f}  {icon}")
        print(f"    Q: {r['question']}")
        print(f"    A: {r['answer'][:120]}...")
        print(f"    Source: {r['source']}")