"""Pre-compute topic prototype embeddings using sentence-transformers.

Run this locally (where the model is available) whenever TOPIC_DEFINITIONS change.
The output file is committed to the repo and loaded at runtime instead of
calling the embedding model.

Usage:
    python scripts/precompute-prototypes.py
"""

import json
import sys
from pathlib import Path

# Add the worker package so imports resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps" / "worker"))

from app.services.topics import TOPIC_DEFINITIONS  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "apps" / "worker" / "app" / "services" / "prototypes.json"


def main() -> None:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers is required. Install it with:")
        print("  pip install sentence-transformers")
        sys.exit(1)

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # Collect all texts to embed: prototype strings + slug fallbacks
    slugs = []
    texts = []

    for definition in TOPIC_DEFINITIONS:
        slugs.append(definition["slug"])
        texts.append(definition["prototype"])

    print(f"Embedding {len(texts)} topic prototypes...")
    embeddings = model.encode(texts, normalize_embeddings=True)

    prototypes = {}
    for slug, embedding in zip(slugs, embeddings):
        prototypes[slug] = [round(float(v), 8) for v in embedding]

    OUTPUT_PATH.write_text(json.dumps(prototypes, indent=2) + "\n")
    print(f"Wrote {len(prototypes)} prototypes to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
