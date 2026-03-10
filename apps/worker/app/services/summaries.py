from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import settings


SummarySource = str


def default_bedrock_base_url(region: str) -> str:
    return f"https://bedrock-mantle.{region}.api.aws/v1"


def resolve_bedrock_base_url() -> str:
    return settings.bedrock_base_url.rstrip("/") if settings.bedrock_base_url else default_bedrock_base_url(settings.bedrock_region)


def build_extractive_summary(abstract: str) -> str:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", abstract) if sentence.strip()]
    if not sentences:
        return ""

    return " ".join(sentences[:2])


def can_call_bedrock() -> bool:
    return settings.summary_provider == "bedrock" and bool(settings.bedrock_api_key)


def _extract_content(message_content: Any) -> str:
    if isinstance(message_content, str):
        return message_content.strip()

    if isinstance(message_content, list):
        parts: list[str] = []
        for item in message_content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item["text"].strip())
        return " ".join(part for part in parts if part)

    return ""


def generate_bedrock_summary(title: str, abstract: str) -> str:
    prompt = (
        "Summarize this arXiv paper for an ML researcher in exactly two concise sentences. "
        "Use only the supplied title and abstract. Do not invent datasets, results, or conclusions."
    )
    payload = {
        "model": settings.summary_model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Title: {title}\n\nAbstract: {abstract}"},
        ],
        "temperature": 0.2,
        "max_completion_tokens": 180,
    }
    request = Request(
        url=f"{resolve_bedrock_base_url()}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.bedrock_api_key}",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Bedrock summary request failed: {exc}") from exc

    choices = body.get("choices") or []
    if not choices:
        raise RuntimeError("Bedrock summary request returned no choices")

    message = choices[0].get("message", {})
    content = _extract_content(message.get("content"))
    if not content:
        raise RuntimeError("Bedrock summary request returned empty content")

    return content


def get_or_create_summary(connection, paper_id: str, title: str, abstract: str) -> tuple[str, SummarySource]:
    with connection.cursor() as cursor:
        cursor.execute(
            "select provider, content from paper_summaries where paper_id = %s limit 1",
            (paper_id,),
        )
        row = cursor.fetchone()

    if row:
        return row["content"], "llm" if row.get("provider") else "extractive"

    if not settings.enable_paper_explain:
        return build_extractive_summary(abstract), "extractive"

    if not can_call_bedrock():
        return build_extractive_summary(abstract), "extractive"

    try:
        summary = generate_bedrock_summary(title, abstract)
    except RuntimeError:
        return build_extractive_summary(abstract), "extractive"

    with connection.cursor() as cursor:
        cursor.execute(
            """
            insert into paper_summaries (paper_id, provider, model, content)
            values (%s, %s, %s, %s)
            on conflict (paper_id)
            do update set
              provider = excluded.provider,
              model = excluded.model,
              content = excluded.content,
              created_at = now()
            """,
            (paper_id, settings.summary_provider, settings.summary_model, summary),
        )
    connection.commit()
    return summary, "llm"
