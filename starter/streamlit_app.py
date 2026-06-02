import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

st.set_page_config(page_title="Research Agent UI", layout="wide")

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

TOOLS = [
    "clarify",
    "timeline",
    "social_search",
    "lookup",
    "fetch",
    "format",
    "send",
    "policy",
    "papers",
    "paper_text",
    "wiki",
    "translate",
    "summarize",
]

PROVIDERS = ["openrouter", "openai", "anthropic", "gemini"]
VERSION_LABELS = {
    "v3": "v3",
    "v2": "v2",
    "v1": "v1",
    "v0": "v0 (baseline)",
}

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm your Research Agent (v3).\nAsk me to look up news, fetch a URL, search tweets, find papers, translate, summarize, or post to Telegram.",
            "tool_calls": [],
        }
    ]
if "stats" not in st.session_state:
    st.session_state.stats = {"turns": 0, "calls": 0, "errors": 0, "last_tools": []}
if "provider" not in st.session_state:
    st.session_state.provider = "openrouter"
if "version" not in st.session_state:
    st.session_state.version = "v3"
elif st.session_state.version not in VERSION_LABELS:
    st.session_state.version = "v0" if "v0" in st.session_state.version else "v3"
if "history" not in st.session_state:
    st.session_state.history = []


def init_transcript() -> None:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([
        safe_slug(st.session_state.version),
        safe_slug(st.session_state.provider),
        timestamp,
    ])
    artifact_version = build_artifact_version(
        st.session_state.version,
        ARTIFACTS_DIR / "system_prompt.md",
        ARTIFACTS_DIR / "tools.yaml",
    )
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": st.session_state.provider,
        "model": None,
        "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
        "tools": str(ARTIFACTS_DIR / "tools.yaml"),
        "history_window": 5,
        "max_tool_rounds": 4,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


if "transcript" not in st.session_state:
    init_transcript()

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  {
  font-family: 'Space Grotesk', sans-serif;
}

body {
  background: linear-gradient(135deg, #f6f2ff 0%, #eef6ff 45%, #fef3e6 100%);
}

#header-bar + div[data-testid="stHorizontalBlock"] {
  background: #1a1a2e;
  color: #fff;
  padding: 10px 14px;
  border-radius: 10px;
  margin-bottom: 12px;
}

#header-bar + div[data-testid="stHorizontalBlock"] label,
#header-bar + div[data-testid="stHorizontalBlock"] .st-emotion-cache-1qg05tj {
  color: #cbd5ff;
  font-size: 0.75rem;
}

#header-bar + div[data-testid="stHorizontalBlock"] input,
#header-bar + div[data-testid="stHorizontalBlock"] select,
#header-bar + div[data-testid="stHorizontalBlock"] .stSelectbox {
  background: #2d2d4e;
  color: #fff;
  border-radius: 6px;
}

.stButton > button {
  background: #c0392b;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
}

.stButton > button:hover {
  background: #a93226;
}

.chat-wrap {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 14px;
  padding: 18px 10px;
  border: 1px solid #e7e7f2;
}

.tool-chip {
  display: inline-block;
  margin: 3px 3px 3px 0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.72rem;
  font-weight: 600;
  background: #e8f0fe;
  color: #1a73e8;
}

.tool-chip.active {
  background: #1a73e8;
  color: #fff;
}

.tool-trace {
  margin-top: 8px;
  padding: 8px 10px;
  background: #f8f9fa;
  border-left: 3px solid #1a73e8;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #555;
}

.tool-trace .tool-name { font-weight: 700; color: #1a73e8; }
.tool-trace .tool-args { color: #888; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.tool-trace .ok  { color: #34a853; }
.tool-trace .err { color: #ea4335; }

.sidebar-card {
  background: #fff;
  border: 1px solid #ececf7;
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
}

.sidebar-title {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #777;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  color: #555;
  font-size: 0.85rem;
}

.msg-note {
  color: #777;
  font-size: 0.8rem;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.markdown('<div id="header-bar"></div>', unsafe_allow_html=True)
header_cols = st.columns([3, 1.2, 1.2, 0.8])
with header_cols[0]:
    st.markdown("### Research Agent")
with header_cols[1]:
    st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(st.session_state.provider), key="provider")
with header_cols[2]:
    st.selectbox(
        "Version",
        list(VERSION_LABELS.keys()),
        index=list(VERSION_LABELS.keys()).index(st.session_state.version),
        key="version",
        format_func=lambda key: VERSION_LABELS[key],
    )
with header_cols[3]:
    if st.button("Clear"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Session cleared.",
                "tool_calls": [],
            }
        ]
        st.session_state.stats = {"turns": 0, "calls": 0, "errors": 0, "last_tools": []}
        st.session_state.history = []
        init_transcript()

with st.sidebar:
    st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Tools</div>", unsafe_allow_html=True)
    active_tools = set(st.session_state.stats.get("last_tools", []))
    tool_html = "".join(
        f"<span class='tool-chip{' active' if t in active_tools else ''}'>{t}</span>"
        for t in TOOLS
    )
    st.markdown(tool_html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Session</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='stat-row'><span>Turns</span><span>{st.session_state.stats['turns']}</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='stat-row'><span>Tool calls</span><span>{st.session_state.stats['calls']}</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div class='stat-row'><span>Errors</span><span>{st.session_state.stats['errors']}</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Last tool</div>", unsafe_allow_html=True)
    last_tools = ", ".join(st.session_state.stats.get("last_tools", [])) or "-"
    st.markdown(f"<div class='msg-note'>{last_tools}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>Lich su (Past Sessions)</div>", unsafe_allow_html=True)

    if TRANSCRIPTS_DIR.exists():
        transcript_files = sorted(
            list(TRANSCRIPTS_DIR.glob("*.json")),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if transcript_files:
            options = {path: path.stem.replace(".transcript", "") for path in transcript_files}
            labels = ["Select to review..."] + [options[path] for path in transcript_files]
            selected_label = st.selectbox("Past sessions", options=labels, index=0)
            selected_file = None
            if selected_label != labels[0]:
                selected_file = next(
                    (path for path, label in options.items() if label == selected_label),
                    None,
                )

            if selected_file and st.button("Load history", use_container_width=True):
                with selected_file.open("r", encoding="utf-8") as handle:
                    loaded_data = json.load(handle)

                st.session_state.messages = []
                st.session_state.history = []
                calls_count = 0
                errors_count = 0
                history_last_tools = []

                for turn in loaded_data.get("turns", []):
                    user_text = turn.get("user", "")
                    assistant_text = turn.get("assistant_text", "")
                    tool_events = turn.get("tool_events", [])

                    reconstructed_tool_calls = []
                    for event in tool_events:
                        status = "err" if "error" in (event.get("result") or {}) else "ok"
                        if status == "err":
                            errors_count += 1
                        calls_count += 1
                        history_last_tools.append(event.get("tool"))
                        reconstructed_tool_calls.append(
                            {
                                "name": event.get("tool"),
                                "args": event.get("args"),
                                "status": status,
                            }
                        )

                    if user_text:
                        st.session_state.messages.append(
                            {"role": "user", "content": user_text, "tool_calls": []}
                        )
                        st.session_state.history.append({"role": "user", "content": user_text})

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": assistant_text,
                            "tool_calls": reconstructed_tool_calls,
                        }
                    )
                    st.session_state.history.append({"role": "assistant", "content": assistant_text})

                st.session_state.stats = {
                    "turns": len(loaded_data.get("turns", [])),
                    "calls": calls_count,
                    "errors": errors_count,
                    "last_tools": list(set(history_last_tools)),
                }
                st.session_state.transcript = loaded_data
                st.session_state.transcript_path = selected_file

                st.rerun()
        else:
            st.markdown("<div class='msg-note'>Chua co lich su nao.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='msg-note'>Chua co lich su nao.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"].replace("\n", "<br/>"), unsafe_allow_html=True)
        tool_calls = msg.get("tool_calls", [])
        for tc in tool_calls:
            status = tc.get("status", "")
            status_cls = "ok" if status == "ok" else "err"
            status_icon = "OK" if status == "ok" else "ERR"
            tool_html = (
                "<div class='tool-trace'>"
                f"<span class='tool-name'>{tc.get('name', '')}</span>"
                f"<span class='tool-args'> ({json.dumps(tc.get('args', {}))})</span>"
                f"<div class='tool-status {status_cls}'>{status_icon} {status}</div>"
                "</div>"
            )
            st.markdown(tool_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

prompt = st.chat_input("Ask something... e.g. Latest tweets from Sam Altman?")


if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "tool_calls": []})
    history_window = st.session_state.transcript.get("history_window", 5)
    max_tool_rounds = st.session_state.transcript.get("max_tool_rounds", 4)
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tool_declarations)

    with st.spinner("Thinking..."):
        try:
            provider = make_provider(st.session_state.provider)
            selected_model = getattr(provider, "default_model", None)
            artifact_version = build_artifact_version(
                st.session_state.version,
                ARTIFACTS_DIR / "system_prompt.md",
                ARTIFACTS_DIR / "tools.yaml",
            )
            st.session_state.transcript.update(artifact_version_dict(artifact_version))
            st.session_state.transcript["provider"] = st.session_state.provider
            st.session_state.transcript["model"] = selected_model

            messages = [
                *trim_history(st.session_state.history, history_window),
                {"role": "user", "content": prompt},
            ]

            result = run_model_tool_loop(
                provider=provider,
                messages=[{"role": "system", "content": system_prompt}, *messages],
                tools=openai_tools,
                model=selected_model,
                max_tool_rounds=max_tool_rounds,
            )

            tool_calls = []
            for event in result.get("tool_events", []):
                status = "err" if "error" in (event.get("result") or {}) else "ok"
                tool_calls.append({"name": event.get("tool"), "args": event.get("args"), "status": status})

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result.get("assistant_text", ""),
                    "tool_calls": tool_calls,
                }
            )

            st.session_state.history.append({"role": "user", "content": prompt})
            st.session_state.history.append({"role": "assistant", "content": result.get("assistant_text", "")})

            st.session_state.stats["turns"] += 1
            st.session_state.stats["calls"] += len(tool_calls)
            st.session_state.stats["last_tools"] = [tc.get("name", "") for tc in tool_calls]

            turn_record = {
                "turn_index": st.session_state.stats["turns"],
                "started_at": now_iso(),
                "user": prompt,
                "status": result.get("status", "answered"),
                "assistant_text": result.get("assistant_text", ""),
                "rounds": result.get("rounds", []),
                "tool_events": result.get("tool_events", []),
                "ended_at": now_iso(),
            }
            st.session_state.transcript["turns"].append(turn_record)
            write_transcript(Path(st.session_state.transcript_path), st.session_state.transcript)
        except Exception as exc:
            st.session_state.stats["errors"] += 1
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": f"Error: {type(exc).__name__}: {exc}",
                    "tool_calls": [],
                }
            )

    st.rerun()
