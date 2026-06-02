from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


def search_wikipedia(person_name: str = "", sentences: int = 5, language: str = "en") -> dict[str, Any]:
    try:
        search_url = f"https://{language}.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": person_name,
            "format": "json",
            "srlimit": 1,
        }
        search_resp = requests.get(search_url, params=search_params, timeout=TIMEOUT)
        search_resp.raise_for_status()
        search_data = search_resp.json()
        results = search_data.get("query", {}).get("search", [])
        if not results:
            return {"tool": "search_wikipedia", "person_name": person_name, "found": False, "content": None}

        page_title = results[0]["pageid"]
        extract_params = {
            "action": "query",
            "prop": "extracts|info",
            "pageids": page_title,
            "exsentences": sentences,
            "exintro": True,
            "explaintext": True,
            "inprop": "url",
            "format": "json",
        }
        extract_resp = requests.get(search_url, params=extract_params, timeout=TIMEOUT)
        extract_resp.raise_for_status()
        extract_data = extract_resp.json()
        pages = extract_data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        return {
            "tool": "search_wikipedia",
            "person_name": person_name,
            "found": True,
            "title": page.get("title"),
            "url": page.get("fullurl"),
            "content": page.get("extract", ""),
            "language": language,
        }
    except Exception as exc:
        return err("search_wikipedia", exc)
