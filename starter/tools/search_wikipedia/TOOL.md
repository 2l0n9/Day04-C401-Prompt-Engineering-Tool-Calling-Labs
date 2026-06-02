---
name: search_wikipedia
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [person_name, sentences, language]
outputs: [title, url, content, language, found]
side_effect: false
---
# search_wikipedia

Bonus research tool. Fetches the intro section of a Wikipedia article for a
named person or topic. Uses the Wikipedia Action API — no API key required.

Set `language` to any Wikipedia language code (e.g. `vi`, `fr`, `ja`) to fetch
a non-English edition. Default is `en`.

Use this tool when the user explicitly asks for Wikipedia content and wants the
full intro text. For a short one-paragraph summary, use `summarize_wikipedia`
instead.
