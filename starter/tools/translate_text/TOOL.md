---
name: translate_text
track: bonus
kind: live_api
provider: MyMemory API
requires_env: []
inputs: [text, target_language, source_language]
outputs: [translated, original, source_language, target_language]
side_effect: false
---
# translate_text

Bonus utility tool. Translates text to the language the user requests via the
MyMemory free translation API — no API key required.

Accepts full language names (`vietnamese`, `japanese`, `korean`, etc.) or ISO
codes (`vi`, `ja`, `ko`). The tool maps common names to codes internally.

Free tier limit: ~5,000 characters per day per IP. For long texts the tool
splits requests into ≤450-character chunks automatically.

Call only when the user explicitly asks for a translation or requests the result
in a specific language. Do not auto-translate tool results unprompted.
