---
name: summarize_wikipedia
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [person_name, max_sentences, language]
outputs: [title, url, description, summary, language, found]
side_effect: false
---
# summarize_wikipedia

Bonus research tool. Returns a concise summary of a Wikipedia article using the
Wikipedia REST `/page/summary` endpoint — no API key required.

Prefer this tool over `search_wikipedia` when the user asks for a short intro,
a quick bio, or a one-paragraph description. For the full intro section use
`search_wikipedia` instead.

If the REST endpoint returns 404, the tool falls back to the Action API search
to find the correct page title and retries.
