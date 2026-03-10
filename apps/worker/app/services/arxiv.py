from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import urlopen
import re
import xml.etree.ElementTree as ET


logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
REQUEST_DELAY_SECONDS = 3.5
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def canonicalize_identifier(identifier: str) -> tuple[str, int]:
    raw = identifier.rstrip("/").split("/")[-1]
    match = re.match(r"(?P<base>.+)v(?P<version>\d+)$", raw)
    if not match:
        return raw, 1

    return match.group("base"), int(match.group("version"))


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def parse_entry(entry: ET.Element) -> dict[str, Any]:
    identifier = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
    canonical_id, version = canonicalize_identifier(identifier)
    title = normalize_whitespace(entry.findtext("atom:title", default="", namespaces=ATOM_NS))
    abstract = normalize_whitespace(entry.findtext("atom:summary", default="", namespaces=ATOM_NS))
    authors = [
        normalize_whitespace(author.findtext("atom:name", default="", namespaces=ATOM_NS))
        for author in entry.findall("atom:author", namespaces=ATOM_NS)
    ]
    categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", namespaces=ATOM_NS)]
    primary_category = categories[0] if categories else "unknown"

    return {
        "canonical_arxiv_id": canonical_id,
        "arxiv_version": version,
        "source_id": f"{canonical_id}v{version}",
        "title": title,
        "abstract": abstract,
        "authors": [author for author in authors if author],
        "categories": [category for category in categories if category],
        "primary_category": primary_category,
        "published_at": parse_datetime(entry.findtext("atom:published", default="", namespaces=ATOM_NS)),
        "updated_at": parse_datetime(entry.findtext("atom:updated", default="", namespaces=ATOM_NS)),
        "url": identifier,
    }


def parse_feed(xml_payload: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_payload)
    entries = root.findall("atom:entry", namespaces=ATOM_NS)
    return [parse_entry(entry) for entry in entries]


def build_query(categories: list[str], max_results: int) -> str:
    category_query = " OR ".join(f"cat:{category}" for category in categories)
    return (
        f"{ARXIV_API_URL}?search_query={quote_plus(category_query)}"
        f"&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    )


def fetch_recent_entries(categories: list[str], max_results_per_category: int = 100) -> list[dict[str, Any]]:
    entries: dict[tuple[str, int], dict[str, Any]] = {}

    for index, category in enumerate(categories):
        if index > 0:
            time.sleep(REQUEST_DELAY_SECONDS)

        category_entries = _fetch_entries_for_categories([category], max_results=max_results_per_category)
        for entry in category_entries:
            key = (entry["canonical_arxiv_id"], entry["arxiv_version"])
            existing = entries.get(key)
            if existing is None or entry["published_at"] > existing["published_at"]:
                entries[key] = entry

    return sorted(entries.values(), key=lambda item: item["published_at"], reverse=True)


def _fetch_entries_for_categories(categories: list[str], max_results: int) -> list[dict[str, Any]]:
    url = build_query(categories, max_results=max_results)

    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(url, timeout=30) as response:
                payload = response.read()
            return parse_feed(payload)
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == MAX_RETRIES - 1:
                logger.error("arXiv API request failed after %d retries: %s", MAX_RETRIES, exc)
                raise
            wait = RETRY_BACKOFF_SECONDS * (attempt + 1)
            logger.warning("arXiv API request failed (attempt %d/%d), retrying in %.1fs: %s", attempt + 1, MAX_RETRIES, wait, exc)
            time.sleep(wait)

    return []
