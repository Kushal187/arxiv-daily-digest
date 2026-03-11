from __future__ import annotations

from functools import lru_cache
from typing import Any

from .embeddings import embed_text
from .similarity import cosine_similarity


TOPIC_DEFINITIONS = [
    {
        "slug": "retrieval-rag",
        "label": "Retrieval / RAG",
        "area_slug": "nlp",
        "prototype": "retrieval augmented generation dense retrieval reranking indexing search systems",
        "keywords": {
            "rag": 1.0,
            "retrieval augmented": 1.0,
            "dense retrieval": 0.9,
            "reranker": 0.85,
            "reranking": 0.85,
            "retriever": 0.8,
            "indexing": 0.5,
            "vector database": 0.75,
        },
        "categories": {"cs.IR": 0.22, "cs.CL": 0.12, "cs.AI": 0.1},
    },
    {
        "slug": "llm-evaluation",
        "label": "LLM Evaluation",
        "area_slug": "nlp",
        "prototype": "llm evaluation benchmarks judge models robustness leaderboard analysis",
        "keywords": {
            "benchmark": 0.8,
            "evaluation": 0.9,
            "judge model": 1.0,
            "eval": 0.7,
            "robustness": 0.75,
            "leaderboard": 0.85,
        },
        "categories": {"cs.CL": 0.18, "cs.AI": 0.12},
    },
    {
        "slug": "agent-systems",
        "label": "Agent Systems",
        "area_slug": "nlp",
        "prototype": "agent systems tool use autonomous workflows multi agent task execution language model agents",
        "keywords": {
            "agent": 0.75,
            "tool use": 0.95,
            "planning agent": 0.9,
            "agent planning": 0.9,
            "multi-agent": 0.95,
            "autonomous workflow": 0.95,
        },
        "categories": {"cs.AI": 0.22, "cs.CL": 0.08},
    },
    {
        "slug": "reasoning-planning",
        "label": "Reasoning / Planning",
        "area_slug": "nlp",
        "prototype": "reasoning planning tree search decomposition long horizon decision making chain of thought",
        "keywords": {
            "reasoning": 0.8,
            "planning": 0.8,
            "tree search": 0.95,
            "decomposition": 0.7,
            "chain of thought": 0.95,
        },
        "categories": {"cs.AI": 0.18, "cs.CL": 0.12},
    },
    {
        "slug": "pure-cv",
        "label": "Pure Computer Vision",
        "area_slug": "computer-vision",
        "prototype": "computer vision detection segmentation recognition classification visual perception",
        "keywords": {
            "object detection": 1.0,
            "segmentation": 0.9,
            "classification": 0.65,
            "visual recognition": 0.8,
            "detection": 0.7,
        },
        "categories": {"cs.CV": 0.26},
    },
    {
        "slug": "diffusion-generative",
        "label": "Diffusion / Generative Vision",
        "area_slug": "computer-vision",
        "prototype": "diffusion generative modeling score matching image synthesis generation visual generation",
        "keywords": {
            "diffusion": 1.0,
            "score matching": 0.95,
            "generative model": 0.85,
            "image synthesis": 0.9,
        },
        "categories": {"cs.CV": 0.16, "cs.LG": 0.12},
    },
    {
        "slug": "reconstruction-3d",
        "label": "3D Reconstruction",
        "area_slug": "vision-3d",
        "prototype": "3d reconstruction nerf neural rendering geometry reconstruction point clouds depth estimation",
        "keywords": {
            "3d reconstruction": 1.0,
            "neural radiance field": 1.0,
            "nerf": 0.95,
            "point cloud": 0.85,
            "depth estimation": 0.75,
        },
        "categories": {"cs.CV": 0.18},
    },
    {
        "slug": "scene-understanding-3d",
        "label": "3D Scene Understanding",
        "area_slug": "vision-3d",
        "prototype": "3d scene understanding embodied perception spatial reasoning mapping geometry",
        "keywords": {
            "scene understanding": 0.9,
            "3d perception": 1.0,
            "slam": 0.85,
            "spatial reasoning": 0.85,
            "mapping": 0.7,
        },
        "categories": {"cs.CV": 0.18, "cs.RO": 0.08},
    },
    {
        "slug": "multimodal-vlm",
        "label": "Vision-Language / Multimodal",
        "area_slug": "multimodal",
        "prototype": "multimodal vision language models image text reasoning video language cross modal",
        "keywords": {
            "vision-language": 1.0,
            "multimodal": 0.85,
            "image-text": 0.85,
            "vlm": 0.95,
            "video-language": 0.95,
        },
        "categories": {"cs.CV": 0.2, "cs.CL": 0.14},
    },
    {
        "slug": "information-retrieval",
        "label": "Information Retrieval",
        "area_slug": "information-retrieval",
        "prototype": "information retrieval search ranking ad hoc retrieval web search relevance recommendation retrieval",
        "keywords": {
            "search ranking": 1.0,
            "retrieval": 0.7,
            "ranking model": 0.85,
            "ad hoc retrieval": 1.0,
            "web search": 0.9,
        },
        "categories": {"cs.IR": 0.28},
    },
    {
        "slug": "graph-learning",
        "label": "Graph Learning",
        "area_slug": "graph-ml",
        "prototype": "graph learning graph neural networks graph transformers structured reasoning",
        "keywords": {
            "graph neural": 1.0,
            "gnn": 0.8,
            "graph learning": 0.95,
            "heterogeneous graph": 0.85,
            "graph transformer": 0.95,
        },
        "categories": {"cs.LG": 0.18},
    },
    {
        "slug": "reinforcement-learning",
        "label": "Reinforcement Learning",
        "area_slug": "reinforcement-learning",
        "prototype": "reinforcement learning policy optimization actor critic offline rl decision making",
        "keywords": {
            "reinforcement learning": 1.0,
            "policy optimization": 0.85,
            "offline rl": 0.95,
            "actor-critic": 0.9,
        },
        "categories": {"cs.LG": 0.22, "cs.AI": 0.08},
    },
    {
        "slug": "robotics",
        "label": "Robotics",
        "area_slug": "robotics",
        "prototype": "robotics embodied control manipulation locomotion robot learning planning",
        "keywords": {
            "robot": 0.7,
            "manipulation": 0.85,
            "locomotion": 0.85,
            "embodied": 0.8,
            "grasping": 0.85,
        },
        "categories": {"cs.RO": 0.24, "cs.AI": 0.08},
    },
    {
        "slug": "speech-audio",
        "label": "Speech / Audio",
        "area_slug": "speech-audio",
        "prototype": "speech audio recognition generation speech language modeling asr tts",
        "keywords": {
            "speech": 0.7,
            "audio": 0.7,
            "asr": 0.95,
            "tts": 0.95,
            "speaker": 0.55,
        },
        "categories": {"eess.AS": 0.24, "cs.CL": 0.08},
    },
    {
        "slug": "learning-theory",
        "label": "Learning Theory",
        "area_slug": "theoretical-ml",
        "prototype": "learning theory optimization theory generalization guarantees scaling laws theoretical machine learning",
        "keywords": {
            "generalization": 0.8,
            "convergence": 0.75,
            "theorem": 0.7,
            "sample complexity": 0.95,
            "optimization theory": 0.95,
            "scaling law": 0.85,
        },
        "categories": {"cs.LG": 0.18, "stat.ML": 0.18},
    },
    {
        "slug": "mechanistic-interpretability",
        "label": "Mechanistic Interpretability",
        "area_slug": "interpretability",
        "prototype": "mechanistic interpretability probing circuits saliency concept discovery model explanations",
        "keywords": {
            "mechanistic interpretability": 1.0,
            "probing": 0.8,
            "saliency": 0.75,
            "circuits": 0.9,
            "interpretability": 0.8,
        },
        "categories": {"cs.CL": 0.1, "cs.LG": 0.12, "cs.AI": 0.08},
    },
    {
        "slug": "training-efficiency",
        "label": "Training Efficiency",
        "area_slug": "training-systems-efficiency",
        "prototype": "training efficiency quantization distillation efficient finetuning inference optimization systems",
        "keywords": {
            "quantization": 1.0,
            "distillation": 0.85,
            "lora": 0.9,
            "parameter-efficient": 0.95,
            "inference optimization": 0.9,
        },
        "categories": {"cs.LG": 0.18, "cs.CL": 0.08},
    },
    {
        "slug": "safety-alignment",
        "label": "Safety / Alignment",
        "area_slug": "safety-alignment",
        "prototype": "safety alignment reward modeling red teaming safeguards misuse prevention",
        "keywords": {
            "alignment": 0.85,
            "red team": 0.85,
            "jailbreak": 0.9,
            "safety": 0.8,
            "reward modeling": 0.95,
        },
        "categories": {"cs.AI": 0.16, "cs.CL": 0.08},
    },
    {
        "slug": "medical-imaging",
        "label": "Medical Imaging",
        "area_slug": "medical-bio-ml",
        "prototype": "medical imaging radiology pathology clinical vision diagnosis support bio medical machine learning",
        "keywords": {
            "medical imaging": 1.0,
            "radiology": 0.9,
            "mri": 0.75,
            "ct": 0.65,
            "ultrasound": 0.7,
            "pathology": 0.75,
        },
        "categories": {"cs.CV": 0.14},
    },
]

AREA_LABELS = {
    "nlp": "NLP",
    "computer-vision": "Computer Vision",
    "vision-3d": "3D Vision",
    "multimodal": "Multimodal",
    "information-retrieval": "Information Retrieval / Search",
    "reinforcement-learning": "Reinforcement Learning",
    "robotics": "Robotics",
    "speech-audio": "Speech / Audio",
    "graph-ml": "Graph ML",
    "theoretical-ml": "Theoretical ML",
    "interpretability": "Interpretability",
    "training-systems-efficiency": "Training / Systems / Efficiency",
    "safety-alignment": "Safety / Alignment",
    "medical-bio-ml": "Medical / Bio ML",
}

HIDE_THRESHOLD = 0.45


def area_for_topic_slug(slug: str) -> str | None:
    for definition in TOPIC_DEFINITIONS:
        if definition["slug"] == slug:
            return str(definition["area_slug"])

    return None


def label_for_topic_slug(slug: str) -> str:
    for definition in TOPIC_DEFINITIONS:
        if definition["slug"] == slug:
            return str(definition["label"])

    return slug


def label_for_area_slug(slug: str) -> str:
    return AREA_LABELS.get(slug, slug)


def _normalize_similarity(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _keyword_score(text: str, keywords: dict[str, float]) -> float:
    total = 0.0
    for phrase, weight in keywords.items():
        if phrase in text:
            total += weight

    return min(total / 2.2, 1.0)


def _category_score(categories: list[str], priors: dict[str, float]) -> float:
    total = sum(priors.get(category, 0.0) for category in categories)
    return min(total / 0.32, 1.0)


@lru_cache(maxsize=None)
def _topic_prototype(slug: str) -> list[float]:
    for definition in TOPIC_DEFINITIONS:
        if definition["slug"] == slug:
            return embed_text(definition["prototype"])

    return [0.0] * 384


def infer_topics(
    title: str,
    abstract: str,
    categories: list[str],
    embedding: list[float] | None = None,
) -> list[dict[str, Any]]:
    text = f"{title.lower()} {abstract.lower()}"
    paper_embedding = embedding if embedding is not None else embed_text(f"{title}\n\n{abstract}")
    predictions: list[dict[str, Any]] = []

    for definition in TOPIC_DEFINITIONS:
        prototype_score = _normalize_similarity(
            cosine_similarity(paper_embedding, _topic_prototype(definition["slug"]))
        )
        keyword_score = _keyword_score(text, definition["keywords"])
        category_score = _category_score(categories, definition["categories"])
        confidence = round(
            min(prototype_score * 0.55 + keyword_score * 0.30 + category_score * 0.15, 0.99),
            3,
        )

        if confidence <= 0:
            continue

        predictions.append(
            {
                "slug": definition["slug"],
                "area_slug": definition["area_slug"],
                "confidence": confidence,
                "is_hidden": confidence < HIDE_THRESHOLD,
                "source": "hybrid-label",
            }
        )

    predictions.sort(key=lambda item: item["confidence"], reverse=True)
    return predictions[:4]
