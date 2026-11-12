"""Snowflake-style (Cortex Analyst-like) chat UI for open-analyst.

Run the API first:  venv/bin/uvicorn app.main:app --port 8000
Then:               venv/bin/streamlit run ui.py
"""
import os

import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
SF_BLUE, SF_DARK = "#29B5E8", "#11567F"

st.set_page_config(page_title="Analyst", page_icon="❄️", layout="wide")

st.markdown(
    f"""
<style>
#MainMenu, footer {{visibility: hidden;}}
.block-container {{padding-top: 1.2rem; max-width: 1100px;}}
.topbar {{background:{SF_DARK}; color:white; padding:14px 22px; border-radius:10px;
         display:flex; align-items:center; gap:12px; margin-bottom:18px;}}
.topbar .logo {{font-size:1.5rem;}}
.topbar .title {{font-size:1.15rem; font-weight:600;}}
.topbar .sub {{opacity:.75; font-size:.85rem; margin-left:auto;}}
[data-testid="stSidebar"] {{background:#F3F8FB; border-right:1px solid #DCE9F0;}}
.stButton>button {{border:1px solid {SF_BLUE}; color:{SF_DARK}; background:white;
                  border-radius:8px; text-align:left;}}
.stButton>button:hover {{background:{SF_BLUE}; color:white; border-color:{SF_BLUE};}}
[data-testid="stChatMessage"] {{background:#F8FBFD; border:1px solid #E3EEF4; border-radius:12px;}}
.chip {{display:inline-block; background:#E6F6FC; color:{SF_DARK}; border-radius:12px;
       padding:2px 10px; font-size:.75rem; margin-right:6px;}}
</style>
<div class="topbar"><span class="logo">❄️</span>
<span class="title">Analyst</span>
<span class="sub">Semantic view: E_commerce · olist.public</span></div>
""",
    unsafe_allow_html=True,
)

SUGGESTIONS = [
    "How many orders were placed per month in 2017?",
    "Top 5 product categories by GMV",
    "Average review score by customer state",
    "What share of payments is each payment type?",
    "Average delivery days by customer state",
    "How many repeat customers do we have?",
]

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("### ❄️ Analyst")
    st.caption("Ask questions about the Olist e-commerce data in plain English.")
    st.markdown("**Suggested questions**")
    picked = None
    for s in SUGGESTIONS:
        if st.button(s, use_container_width=True):
            picked = s
    st.divider()
    try:
        ok = requests.get(f"{API}/health", timeout=2).ok
    except requests.RequestException:
        ok = False
    st.markdown(f"API: {'🟢 connected' if ok else '🔴 offline'}")
    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


def render_result(m: dict):
    st.markdown(f'<span class="chip">Generated SQL</span>', unsafe_allow_html=True)
    with st.expander("View SQL", expanded=False):
        st.code(m["sql"], language="sql")
    df = pd.DataFrame(m["rows"], columns=m["columns"])
    if df.empty:
        st.info("The query returned no rows.")
        return
    tab_t, tab_c = st.tabs(["Results", "Chart"])
    with tab_t:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{m['row_count']} rows")
    with tab_c:
        num = df.select_dtypes("number").columns.tolist()
        if len(df.columns) >= 2 and num:
            x = next((c for c in df.columns if c not in num), df.columns[0])
            y = num[0] if num[0] != x else (num[1] if len(num) > 1 else None)
            if y:
                chart = df.set_index(x)[[y]]
                (st.line_chart if "month" in x.lower() or "date" in x.lower() else st.bar_chart)(
                    chart, color=SF_BLUE
                )
                return
        st.caption("No numeric column to chart.")


if not st.session_state.messages:
    st.markdown("#### What would you like to know?")
    st.caption("Pick a suggestion on the left or type a question below.")

for m in st.session_state.messages:
    with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "❄️"):
        if m["role"] == "user":
            st.write(m["content"])
        elif m.get("error"):
            st.error(m["error"])
            if m.get("sql"):
                st.code(m["sql"], language="sql")
        else:
            render_result(m)

question = st.chat_input("Ask a question about your data") or picked
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(question)
    with st.chat_message("assistant", avatar="❄️"):
        with st.spinner("Generating SQL and running it…"):
            try:
                r = requests.post(f"{API}/query", json={"question": question}, timeout=300)
                if r.ok:
                    msg = {"role": "assistant", **r.json()}
                    render_result(msg)
                else:
                    d = r.json().get("detail")
                    msg = {"role": "assistant",
                           "error": d.get("error") if isinstance(d, dict) else str(d),
                           "sql": d.get("sql") if isinstance(d, dict) else None}
                    st.error(msg["error"])
                    if msg["sql"]:
                        st.code(msg["sql"], language="sql")
            except requests.RequestException as e:
                msg = {"role": "assistant", "error": f"Cannot reach API: {e}"}
                st.error(msg["error"])
    st.session_state.messages.append(msg)
