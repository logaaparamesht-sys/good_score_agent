"""
dashboard/app.py  –  Streamlit UI for the GoodScore Support AI prototype.

Talks to ai_backend over HTTP; never touches Postgres.
"""

import json
import os

import requests
import streamlit as st

AI_BACKEND_URL = os.environ.get("AI_BACKEND_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GoodScore AI Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a polished, premium look
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Hide Streamlit top header, deploy button, and footer */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0c29 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #e0e0ff;
    }

    .stChatMessage {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102,126,234,0.4);
    }

    .header-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
    }
    .badge-lean {
        background: rgba(46, 213, 115, 0.15);
        color: #2ed573;
        border: 1px solid rgba(46, 213, 115, 0.3);
    }
    .badge-agent {
        background: rgba(255, 165, 2, 0.15);
        color: #ffa502;
        border: 1px solid rgba(255, 165, 2, 0.3);
    }

    .tool-card {
        background: rgba(102, 126, 234, 0.08);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }
    .tool-card .tool-name {
        color: #667eea;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("# 💳 GoodScore AI")
    st.markdown("---")

    customer_id = st.selectbox(
        "Select Customer ID",
        options=["C001", "C002", "C003", "C004", "C005"],
        index=0,
        help="Select a customer profile (C001=Good, C002=Needs work, C003=Excellent, C004=Poor, C005=Recovery)"
    )

    mode = st.radio(
        "Pipeline Mode",
        options=["Agentic (Tool-calling)", "Lean (Pre-fetch)"],
        index=0,
        help=(
            "**Agentic**: LLM dynamically decides tools to call (supports all 18 flows).\n\n"
            "**Lean**: Pre-fetches key profile context into prompt for single fast call."
        ),
    )

    st.markdown("---")
    st.markdown("**Sample Quick Prompts**")
    sample_prompts = [
        "What is my credit score and how can I improve it?",
        "Show my 12-month score trend summary.",
        "What pending bills do I have and can you pay my Tata Power bill?",
        "Are there any hard credit enquiries on my profile?",
        "Am I eligible for a personal or home loan?",
        "Draft an NOC request letter for my closed loan.",
        "Convert my overdue EMI into a restructured plan."
    ]
    for sp in sample_prompts:
        if st.button(sp, key=sp):
            st.session_state.preset_prompt = sp

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.preset_prompt = None
        st.rerun()

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
is_lean = mode.startswith("Lean")
mode_badge = (
    '<span class="header-badge badge-lean">⚡ LEAN</span>'
    if is_lean
    else '<span class="header-badge badge-agent">🤖 AGENTIC</span>'
)
st.markdown(
    f"<h2 style='color:#e0e0ff'>GoodScore Financial Assistant {mode_badge}</h2>",
    unsafe_allow_html=True,
)
st.caption(f"Active Customer: **{customer_id}** | 18 Flows Supported")

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                st.markdown(
                    f'<div class="tool-card">'
                    f'<span class="tool-name">🔧 {tc["tool"]}</span> '
                    f'<code>{json.dumps(tc["args"])}</code><br>'
                    f'<small>{tc.get("preview", "")}</small>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
prompt_input = st.chat_input("Ask GoodScore AI about scores, bills, disputes, loans...")

# Handle preset prompt click if available
if st.session_state.preset_prompt:
    prompt = st.session_state.preset_prompt
    st.session_state.preset_prompt = None
else:
    prompt = prompt_input

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
    ]

    endpoint = "/chat" if is_lean else "/agent-chat"
    url = f"{AI_BACKEND_URL}{endpoint}"
    payload = {
        "customer_id": customer_id,
        "message": prompt,
        "conversation_history": history,
    }

    with st.chat_message("assistant"):
        response_text = ""
        tool_calls = []
        placeholder = st.empty()

        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if "content" in data:
                        response_text += data["content"]
                        placeholder.markdown(response_text + "▌")

                    if "tool_call" in data:
                        tool_calls.append(
                            {
                                "tool": data["tool_call"],
                                "args": data.get("args", {}),
                                "preview": data.get("result_preview", ""),
                            }
                        )
                        with st.expander(f"🔧 Tool Execution: `{data['tool_call']}`", expanded=False):
                            st.json(data.get("args", {}))
                            st.text(data.get("result_preview", "")[:300])

            placeholder.markdown(response_text)

        except requests.exceptions.ConnectionError:
            response_text = f"⚠️ Could not connect to backend at `{AI_BACKEND_URL}`. Ensure containers are running."
            placeholder.markdown(response_text)
        except Exception as e:
            response_text = f"⚠️ Error: {e}"
            placeholder.markdown(response_text)

    msg_data = {"role": "assistant", "content": response_text}
    if tool_calls:
        msg_data["tool_calls"] = tool_calls
    st.session_state.messages.append(msg_data)
