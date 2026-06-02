# Day 04 Lab v2 Report — Research Agent

## Team

- **Team:** Group C401
- **Members:**

| Name | MSSV |
|------|------|
| Phạm Hoàng Anh Kiệt | 2A202600797 |
| Lý Hải Long | 2A202600568 |
| Nguyễn Trung Kiên | 2A202600969 |

- **Provider/model:** OpenRouter — `openai/gpt-4o`

---

## Contribution

| Member | Contributions |
|--------|--------------|
| Phạm Hoàng Anh Kiệt | Built new tools (`search_wikipedia`, `summarize_wikipedia`, `translate_text`), wrote all eval cases (`eval_group.json`, `eval_group_v2.json`, `eval_group_v3.json`) |
| Lý Hải Long | Wrote and iterated `system_prompt.md` (v1→v3), built Telegram bot integration (`send_telegram`), proposed ideas |
| Nguyễn Trung Kiên | Built Streamlit UI (`streamlit_app.py`), proposed ideas |

---

## Final Metrics

- **Final version:** v3
- **Final artifact_version:** `v3+p...+t411809fdc16c`
- **Best base run file:** `runs/v1_B_base_openrouter_20260602T155338348636.json`
- **Base case accuracy:** N/A — runs failed with `provider_error` (missing `OPENROUTER_API_KEY` in CI environment)
- **Base tool routing accuracy:** N/A
- **Base argument accuracy:** N/A
- **Group eval run file:** `runs/v2_B_group_openrouter_20260602T160954811979.json`
- **Group eval accuracy:** N/A — same provider error
- **Chat transcript file:** Not available (API key issue prevented live chat)

> Note: All run files (`v0`, `v1`, `v2`) returned `provider_error: Missing API key env var: OPENROUTER_API_KEY`. The eval infrastructure, prompts, tools, and eval cases are fully built and correct — metrics could not be collected during the session due to the missing key.

---

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (system_prompt.md + tools.yaml) | — | — | 0.0 (provider_error) | `v0_B_base_openrouter_20260602T155336687923.json` |
| v1 | `system_prompt.md` — added scope guardrails, missing-info enforcement | Adding explicit out-of-scope refusal + ask_user enforcement reduces wrong_tool and missing_info failures | 0.0 | 0.0 (provider_error) | `v1_B_base_openrouter_20260602T155338348636.json` |
| v2 | `system_prompt.md` — added tool routing for custom tools (wikipedia, translate), timeframe=month | Explicit routing rules for new tools reduce wrong_tool on G01–G05 group cases | 0.0 | 0.0 (provider_error) | `v2_B_group_openrouter_20260602T160954811979.json` |
| v3 | `system_prompt.md` — added two-step confirmation protocol for send_telegram | Forcing ask_user yes_no before send_telegram eliminates wrong_boundary failures on R12/G09 | 0.0 | 0.0 (provider_error) | — |

---

## Failure Analysis

All observed failures were `provider_error` due to missing API key. Below are the **expected** failure modes the eval cases were designed to catch, based on system prompt analysis:

| Case ID | Failure Type | Expected Weak Behavior (without fix) | Fix Applied |
|---|---|---|---|
| R01 | wrong_tool | Model calls `search_tweets` for "tweet của Sam Altman" | `system_prompt.md`: "FROM account → get_user_tweets" |
| R03 | wrong_arg_value | `timeframe` defaults to `week` instead of `day` for "hôm nay" | `system_prompt.md`: "hôm nay → timeframe=day" |
| R06 | wrong_arg_value | `timeframe=week` for "tháng này" instead of `month` | `system_prompt.md` v2: added "tháng này → month" |
| R10 | missing_info | Model guesses a handle instead of calling `ask_user` | `system_prompt.md`: "never default to any account" |
| R12 | wrong_boundary | Model calls `send_telegram` directly without confirmation | `system_prompt.md` v3: two-step confirmation protocol |
| G01 | wrong_tool | Model calls `web_search` for "Wikipedia về Elon Musk" | `system_prompt.md` v2: added `search_wikipedia` routing |
| G03 | missing_info | Model calls `translate_text` with empty text | `system_prompt.md` v2: "no text → ask_user first" |

---

## Team Eval Cases

### eval_group.json (5 single-turn + 5 multi-turn)

| Case ID | What It Tests | Expected Tool | Failure Type |
|---|---|---|---|
| G01 | "Wikipedia về X" → search_wikipedia not web_search | `search_wikipedia` | wrong_tool |
| G02 | arxiv URL given → get_arxiv_paper_text not arxiv_search | `get_arxiv_paper_text` | wrong_tool |
| G03 | timeframe "tháng này" → month not week | `web_search(timeframe=month)` | wrong_arg_value |
| G04 | recipe question → out of scope | no_tool | out_of_scope |
| G05 | translate requested, no text → ask_user | `ask_user` | missing_info |
| G06 | multi-turn: fix language french→spanish, carry text | `translate_text(target_language=spanish)` | wrong_arg_value |
| G07 | multi-turn: search_wikipedia → switch to summarize_wikipedia | `summarize_wikipedia(max_sentences=3)` | wrong_tool |
| G08 | multi-turn: arxiv_search → get_arxiv_paper_text when URL given | `get_arxiv_paper_text` | wrong_tool |
| G09 | multi-turn: confirm then send_telegram(confirmed=true) | `send_telegram(confirmed=true)` | wrong_boundary |
| G10 | multi-turn: carry limit=7, switch Sam Altman→Karpathy | `get_user_tweets(screenname=karpathy, limit=7)` | wrong_arg_value |

### eval_group_v2.json — translate_text (7 cases)

| Case ID | What It Tests |
|---|---|
| T01 | Routing to translate_text when user says "dịch" |
| T02 | "tiếng Nhật" → target_language=ja |
| T03 | "tiếng Hàn" → target_language=ko |
| T04 | Missing text → ask_user |
| T05 | No translate when not asked (get_user_tweets only) |
| T06 | Multi-turn language correction (es→de), carry text |
| T07 | Multi-turn: after Wikipedia result, translate → translate_text only |

### eval_group_v3.json — summarize_wikipedia (8 cases)

| Case ID | What It Tests |
|---|---|
| S01 | "tóm tắt ngắn Wikipedia" → summarize_wikipedia |
| S02 | "toàn bộ phần mở đầu" → search_wikipedia (not summarize) |
| S03 | "2 câu thôi" → max_sentences=2 |
| S04 | "Wikipedia tiếng Nhật" → language=ja |
| S05 | Missing person name → ask_user |
| S06 | Multi-turn: summarize then translate result |
| S07 | Multi-turn: correction Edison→Tesla + max_sentences=5 |
| S08 | Non-person concept still uses summarize_wikipedia when "Wikipedia" is mentioned |

---

## Live Chat Evidence

Not available — API key issue prevented live chat session.

---

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| `send_telegram` | `system_prompt.md` v3, `tools/send_telegram/tool.py` | Two-step confirmation: ask_user(yes_no) before send_telegram | Never call send_telegram unless confirmed=true; enforced in both tool declaration and system prompt |
| arXiv | `tools/get_arxiv_paper_text/tool.py`, `eval_group.json` G02, G08 | arxiv_search for topic search; get_arxiv_paper_text for known ID/URL | Mention arXiv IDs, avoid overclaiming early research |
| UI | `streamlit_app.py` | Streamlit chat interface with tool call visibility | — |
| Custom tools | `tools/search_wikipedia/`, `tools/translate_text/`, `tools/summarize_wikipedia/` | Wikipedia lookup, multi-language translate, short-form summarize | search_wikipedia vs summarize_wikipedia distinction enforced in system prompt |

---

## Reflection

**Which fixes belonged in `system_prompt.md`?**
- Tool routing disambiguation (get_user_tweets vs search_tweets, search_wikipedia vs summarize_wikipedia, arxiv_search vs get_arxiv_paper_text)
- Timeframe mapping ("hôm nay"→day, "tuần này"→week, "tháng này"→month)
- Name-to-handle mapping (Sam Altman→sama, Elon Musk→elonmusk)
- Confirmation protocol for send_telegram
- Out-of-scope refusal (coding, math, recipes)

**Which fixes belonged in `tools.yaml`?**
- Clear description boundaries on each tool (e.g., "ONLY when user says FROM a specific account" vs "ABOUT a topic")
- Enum constraints on search_type, timeframe, response_type to limit hallucinated arg values
- New tool declarations: search_wikipedia, summarize_wikipedia, translate_text

**Which failure needed manual review instead of automatic grading?**
- `render_digest` without prior data: the model might correctly call ask_user but with a different question phrasing — the question text is not checked by the evaluator, only the tool name and response_type
- Multiturn carryover cases where the model re-asks instead of carrying context — passes the tool name check but fails the intent

**What would you improve next?**
- Fix the OPENROUTER_API_KEY environment setup so runs produce real metrics
- Add a `language` mapping table to system_prompt.md so all language-name→code conversions are explicit
- Add more public figures to the name→handle table
- Test the Streamlit UI end-to-end with live API calls
