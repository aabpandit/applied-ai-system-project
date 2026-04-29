from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "data"
KB_PATH         = DATA_DIR / "rag_knowledge_base.json"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"
METADATA_PATH   = DATA_DIR / "metadata.pkl"

# 384-dim, ~80 MB, fast inference, strong semantic similarity
MODEL_NAME = "all-MiniLM-L6-v2"

_KEEP = (
    "id", "question", "answer",
    "species", "category", "urgency",
    "source", "source_url", "source_type", "tags",
)


def load_knowledge_base(path: Path = KB_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Knowledge base not found at {path}\n"
            "Make sure data/rag_knowledge_base.json exists."
        )
    with open(path, encoding="utf-8-sig") as fh:  # utf-8-sig strips BOM if present
        raw = json.load(fh)
    entries = raw.get("entries", [])
    if not entries:
        raise ValueError(f"No entries found in {path}")
    print(f"[build_index] Loaded {len(entries)} entries from {path.name}")
    return entries


def _retrieval_text(entry: dict) -> str:
    # Combine question + tags so embeddings capture both phrasing and keywords.
    tags = " ".join(entry.get("tags", []))
    return f"{entry['question']} {tags}"


def encode_entries(
    entries: list[dict],
    model_name: str = MODEL_NAME,
) -> tuple[np.ndarray, SentenceTransformer]:
    model = SentenceTransformer(model_name)
    texts = [_retrieval_text(e) for e in entries]
    print(f"[build_index] Encoding {len(texts)} entries with '{model_name}' ...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # unit-length -> cos-sim == dot product
    )
    return embeddings.astype(np.float32), model


def save_index(
    embeddings: np.ndarray,
    entries: list[dict],
    out_dir: Path = DATA_DIR,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    print(
        f"[build_index] Embeddings -> {EMBEDDINGS_PATH} "
        f"shape={embeddings.shape} dtype={embeddings.dtype}"
    )
    metadata = [{k: e[k] for k in _KEEP if k in e} for e in entries]
    with open(METADATA_PATH, "wb") as fh:
        pickle.dump(metadata, fh)
    print(f"[build_index] Metadata   -> {METADATA_PATH} ({len(metadata)} records)")


def load_index(
    embeddings_path: Path = EMBEDDINGS_PATH,
    metadata_path: Path = METADATA_PATH,
) -> tuple[np.ndarray, list[dict]]:
    missing = [p for p in (embeddings_path, metadata_path) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Index files not found: {missing}\n"
            "Run  python build_index.py  to build the index first."
        )
    embeddings = np.load(embeddings_path)
    with open(metadata_path, "rb") as fh:
        metadata = pickle.load(fh)
    print(f"[build_index] Loaded index: {embeddings.shape[0]} entries, dim={embeddings.shape[1]}")
    return embeddings, metadata


def build(
    save: bool = True,
    model_name: str = MODEL_NAME,
) -> tuple[np.ndarray, list[dict], SentenceTransformer]:
    entries = load_knowledge_base()
    embeddings, model = encode_entries(entries, model_name)
    metadata = [{k: e[k] for k in _KEEP if k in e} for e in entries]
    if save:
        save_index(embeddings, entries)
    return embeddings, metadata, model


if __name__ == "__main__":
    build(save=True)
    print("[build_index] Done -- index is ready.")