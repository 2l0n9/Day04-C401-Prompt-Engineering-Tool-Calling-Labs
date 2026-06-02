from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


def summarize_wikipedia(person_name: str = "", max_sentences: int = 3, language: str = "en") -> dict[str, Any]:
    try:
        # Use Wikipedia REST summary endpoint — concise, always intro paragraph
        headers = {"Accept": "application/json", "User-Agent": "ResearchAgent/1.0 (research-lab; contact@example.com)"}
        rest_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(person_name)}"
        resp = requests.get(rest_url, timeout=TIMEOUT, headers=headers)

        if resp.status_code == 404:
            # Fallback: search for the right title then retry
            search_url = f"https://{language}.wikipedia.org/w/api.php"
            search_params = {"action": "query", "list": "search", "srsearch": person_name, "format": "json", "srlimit": 1}
            sr = requests.get(search_url, params=search_params, headers=headers, timeout=TIMEOUT)
            sr.raise_for_status()
            hits = sr.json().get("query", {}).get("search", [])
            if not hits:
                return {"tool": "summarize_wikipedia", "person_name": person_name, "found": False, "summary": None}
            page_title = hits[0]["title"]
            rest_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(page_title)}"
            resp = requests.get(rest_url, timeout=TIMEOUT, headers=headers)

        resp.raise_for_status()
        data = resp.json()
        extract = data.get("extract", "")
        sentences = [s.strip() for s in extract.split(". ") if s.strip()]
        summary = ". ".join(sentences[:max_sentences])
        if summary and not summary.endswith("."):
            summary += "."

        return {
            "tool": "summarize_wikipedia",
            "person_name": person_name,
            "found": True,
            "title": data.get("title"),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
            "description": data.get("description"),
            "summary": summary,
            "language": language,
        }
    except Exception as exc:
        return err("summarize_wikipedia", exc)
