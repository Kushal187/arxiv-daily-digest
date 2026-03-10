from __future__ import annotations

from collections import Counter
from typing import Any


TOPIC_DEFINITIONS = [
    {
        "slug": "retrieval-rag",
        "keywords": ["rag", "retrieval augmented", "dense retrieval", "reranker", "retriever", "vector database"],
        "categories": {"cs.IR": 0.22, "cs.CL": 0.1, "cs.AI": 0.1},
    },
    {
        "slug": "llm-evaluation",
        "keywords": ["benchmark", "evaluation", "judge model", "eval", "robustness", "leaderboard"],
        "categories": {"cs.CL": 0.18, "cs.AI": 0.12},
    },
    {
        "slug": "agent-systems",
        "keywords": ["agent", "tool use", "planning agent", "multi-agent", "autonomous workflow"],
        "categories": {"cs.AI": 0.22, "cs.CL": 0.08},
    },
    {
        "slug": "multimodal-vlm",
        "keywords": ["vision-language", "multimodal", "image-text", "vlm", "video-language"],
        "categories": {"cs.CV": 0.2, "cs.CL": 0.14},
    },
    {
        "slug": "diffusion-generative",
        "keywords": ["diffusion", "score matching", "generative model", "image synthesis"],
        "categories": {"cs.CV": 0.16, "cs.LG": 0.12},
    },
    {
        "slug": "graph-learning",
        "keywords": ["graph neural", "gnn", "graph learning", "heterogeneous graph", "graph transformer"],
        "categories": {"cs.LG": 0.18},
    },
    {
        "slug": "medical-imaging",
        "keywords": ["medical imaging", "radiology", "mri", "ct", "ultrasound", "pathology"],
        "categories": {"cs.CV": 0.14},
    },
    {
        "slug": "reinforcement-learning",
        "keywords": ["reinforcement learning", "policy optimization", "offline rl", "actor-critic"],
        "categories": {"cs.LG": 0.22, "cs.AI": 0.08},
    },
    {
        "slug": "robotics",
        "keywords": ["robot", "manipulation", "locomotion", "embodied", "grasping"],
        "categories": {"cs.RO": 0.24, "cs.AI": 0.08},
    },
    {
        "slug": "speech-audio",
        "keywords": ["speech", "audio", "asr", "tts", "speaker"],
        "categories": {"eess.AS": 0.24, "cs.CL": 0.08},
    },
    {
        "slug": "information-retrieval",
        "keywords": ["search ranking", "retrieval", "ranking model", "ad hoc retrieval", "web search"],
        "categories": {"cs.IR": 0.28},
    },
    {
        "slug": "reasoning-planning",
        "keywords": ["reasoning", "planning", "tree search", "decomposition", "chain of thought"],
        "categories": {"cs.AI": 0.18, "cs.CL": 0.12},
    },
    {
        "slug": "training-efficiency",
        "keywords": ["quantization", "distillation", "lora", "parameter-efficient", "inference optimization"],
        "categories": {"cs.LG": 0.18, "cs.CL": 0.08},
    },
    {
        "slug": "safety-alignment",
        "keywords": ["alignment", "red team", "jailbreak", "safety", "reward modeling"],
        "categories": {"cs.AI": 0.16, "cs.CL": 0.08},
    },
]

HIDE_THRESHOLD = 0.34


def infer_topics(title: str, abstract: str, categories: list[str]) -> list[dict[str, Any]]:
    text = f"{title.lower()} {abstract.lower()}"
    predictions: list[dict[str, Any]] = []

    for definition in TOPIC_DEFINITIONS:
        keyword_hits = Counter(keyword for keyword in definition["keywords"] if keyword in text)
        keyword_score = min(sum(keyword_hits.values()) * 0.22, 0.66)
        category_score = sum(definition["categories"].get(category, 0.0) for category in categories)
        confidence = round(min(keyword_score + category_score, 0.99), 3)

        if confidence <= 0:
            continue

        predictions.append(
            {
                "slug": definition["slug"],
                "confidence": confidence,
                "is_hidden": confidence < HIDE_THRESHOLD,
                "source": "weak-label",
            }
        )

    predictions.sort(key=lambda item: item["confidence"], reverse=True)
    return predictions[:4]
