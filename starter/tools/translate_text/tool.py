from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

# MyMemory free translation API — no key required, 5000 chars/day limit
_MYMEMORY_URL = "https://api.mymemory.translated.net/get"

LANGUAGE_CODES = {
    "english": "en",
    "vietnamese": "vi",
    "french": "fr",
    "spanish": "es",
    "german": "de",
    "japanese": "ja",
    "korean": "ko",
    "chinese": "zh",
    "thai": "th",
    "italian": "it",
    "portuguese": "pt",
    "russian": "ru",
    "arabic": "ar",
    "hindi": "hi",
}


def _resolve_lang(lang: str) -> str:
    key = lang.strip().lower()
    return LANGUAGE_CODES.get(key, key)


def translate_text(text: str = "", target_language: str = "vi", source_language: str = "auto") -> dict[str, Any]:
    try:
        target_code = _resolve_lang(target_language)
        source_code = "auto" if source_language in ("auto", "") else _resolve_lang(source_language)
        lang_pair = f"{source_code}|{target_code}" if source_code != "auto" else f"en|{target_code}"

        # MyMemory has a 500-char limit per request; split if needed
        chunks: list[str] = []
        while len(text) > 450:
            split_at = text.rfind(" ", 0, 450)
            split_at = split_at if split_at > 0 else 450
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip()
        chunks.append(text)

        translated_parts: list[str] = []
        for chunk in chunks:
            resp = requests.get(
                _MYMEMORY_URL,
                params={"q": chunk, "langpair": lang_pair},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            translated_parts.append(data["responseData"]["translatedText"])

        return {
            "tool": "translate_text",
            "source_language": source_code,
            "target_language": target_code,
            "original": " ".join(chunks),
            "translated": " ".join(translated_parts),
        }
    except Exception as exc:
        return err("translate_text", exc)
