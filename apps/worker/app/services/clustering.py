from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import date


STOPWORDS = {
    "the", "and", "for", "with", "from", "using", "into", "towards", "via",
    "based", "new", "large", "language", "model", "models",
    "data", "network", "networks", "neural", "deep", "learning", "method",
    "methods", "approach", "approaches", "system", "systems", "propose",
    "proposed", "results", "performance", "training", "efficient", "analysis",
    "task", "tasks", "framework", "our", "can", "this", "that", "are", "also",
    "which", "show", "use", "paper", "study", "present", "demonstrate",
    "improved", "novel", "existing", "achieve", "state", "art",
}


def _top_terms(texts: list[str]) -> str:
    tokens: list[str] = []
    for text in texts:
        tokens.extend(re.findall(r"[a-z]{3,}", text.lower()))

    counts = Counter(token for token in tokens if token not in STOPWORDS)
    top = [term for term, _ in counts.most_common(3)]
    return " / ".join(top) if top else "misc"


def cluster_papers(papers: list[dict], cluster_date: date) -> dict[str, dict]:
    groups: dict[str, list[dict]] = defaultdict(list)

    for paper in papers:
        visible_topics = [topic for topic in paper["topics"] if not topic["is_hidden"]]
        if visible_topics:
            group_key = f"topic:{visible_topics[0]['slug']}"
        else:
            group_key = f"category:{paper['primary_category']}"

        groups[group_key].append(paper)

    assignments: dict[str, dict] = {}
    for index, (group_key, members) in enumerate(groups.items(), start=1):
        label = _top_terms([f"{paper['title']} {paper['abstract']}" for paper in members])
        cluster_id = f"{cluster_date.isoformat()}-{index}"
        for paper in members:
            assignments[paper["source_id"]] = {
                "cluster_date": cluster_date,
                "cluster_id": cluster_id if len(members) > 1 else "misc",
                "cluster_label": label if len(members) > 1 else "misc",
                "group_key": group_key,
            }

    return assignments
