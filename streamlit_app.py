import pandas as pd
import streamlit as st

# Connection setup
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    IS_SIS = True
except Exception:
    import snowflake.connector
    if "CONN" not in st.session_state:
        st.session_state.CONN = snowflake.connector.connect(
            user="<user>",
            password="<password>",
            account="<account>",
            warehouse="OLYMPICS_WH",
            role="ACCOUNTADMIN",
        )

import requests

DATABASE = "OLYMPICS_ANALYTICS"
SCHEMA = "CORE"
SEMANTIC_VIEW = f"{DATABASE}.{SCHEMA}.OLYMPICS_SEMANTIC_MODEL"

st.set_page_config(page_title="Olympics Analyst", layout="wide", page_icon="🏅")

# Styling
st.markdown("""
<style>
    :root {
        --navy: #0B1F3A;
        --gold: #C9A227;
        --gold-light: #FBF3DA;
        --slate: #5B6472;
        --bg: #F7F8FA;
    }

    .stApp { background-color: var(--bg); }

    .app-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 4px;
    }
    .app-header .icon-box {
        background: var(--navy);
        border: 2px solid var(--gold);
        border-radius: 14px;
        width: 56px;
        height: 56px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
        flex-shrink: 0;
    }
    .app-header h1 {
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--navy);
        margin: 0;
    }
    .app-subtitle {
        color: var(--slate);
        font-size: 0.95rem;
        margin: 4px 0 24px 72px;
    }

    .kpi-row { display: flex; gap: 16px; margin-bottom: 8px; }
    .kpi-card {
        flex: 1;
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(11, 31, 58, 0.06);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--slate);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: var(--navy);
    }

    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #E5E7EB;
    }
    section[data-testid="stSidebar"] button {
        text-align: left !important;
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        color: var(--navy) !important;
        font-size: 0.85rem !important;
    }
    section[data-testid="stSidebar"] button:hover {
        border-color: var(--gold) !important;
        background-color: var(--gold-light) !important;
    }

    div[data-testid="stChatMessage"] {
        border-radius: 14px;
        border: 1px solid #E5E7EB;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# Main functions

def get_host_and_token():
    if IS_SIS:
        conn = session._conn._conn
        return conn.host, conn.rest.token
    else:
        conn = st.session_state.CONN
        return conn.host, conn.rest.token


def run_sql(sql: str) -> pd.DataFrame:
    if IS_SIS:
        return session.sql(sql).to_pandas()
    else:
        cur = st.session_state.CONN.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)


def ask_cortex_analyst(question: str) -> dict:
    host, token = get_host_and_token()
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
        "semantic_view": SEMANTIC_VIEW,
    }
    resp = requests.post(
        url=f"https://{host}/api/v2/cortex/analyst/message",
        json=request_body,
        headers={
            "Authorization": f'Snowflake Token="{token}"',
            "Content-Type": "application/json",
        },
    )
    if resp.status_code < 400:
        return resp.json()
    else:
        raise Exception(f"Cortex Analyst request failed ({resp.status_code}): {resp.text}")


@st.cache_data(ttl=3600, show_spinner=False)
def load_kpis():
    df = run_sql(f"""
        SELECT
            (SELECT COUNT(DISTINCT id) FROM {DATABASE}.{SCHEMA}.ATHLETE_EVENTS) AS athlete_count,
            (SELECT COUNT(*) FROM {DATABASE}.{SCHEMA}.ATHLETE_EVENTS) AS entry_count,
            (SELECT COUNT(medal) FROM {DATABASE}.{SCHEMA}.ATHLETE_EVENTS) AS medal_count,
            (SELECT COUNT(DISTINCT noc) FROM {DATABASE}.{SCHEMA}.ATHLETE_EVENTS) AS country_count
    """)
    return df.iloc[0]


st.markdown("""
<div class="app-header">
    <div class="icon-box">🏅</div>
    <h1>Olympics Historical Analyst</h1>
</div>
<div class="app-subtitle">Ask questions in plain English — powered by Snowflake Cortex Analyst</div>
""", unsafe_allow_html=True)

kpi = load_kpis()
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card">
        <div class="kpi-label">Distinct Athletes</div>
        <div class="kpi-value">{int(kpi['ATHLETE_COUNT']):,}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Athlete-Event Entries</div>
        <div class="kpi-value">{int(kpi['ENTRY_COUNT']):,}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Medals Awarded</div>
        <div class="kpi-value">{int(kpi['MEDAL_COUNT']):,}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">Countries (NOCs)</div>
        <div class="kpi-value">{int(kpi['COUNTRY_COUNT']):,}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.write("")

SUGGESTED_QUESTIONS = [
    "How many athletes have competed?",
    "Which country has won the most gold medals?",
    "What's the average age of athletes by sport?",
    "How has the number of female athletes changed over time?",
    "How many athletes competed for Great Britain?",
    "Which sport has the youngest average age?",
    "What's the medal count by season?",
]

with st.sidebar:
    st.markdown("### Suggested questions")
    for q in SUGGESTED_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"suggest_{q}"):
            st.session_state["pending_question"] = q

    st.divider()
    st.markdown("### Query history")
    if "history" not in st.session_state:
        st.session_state.history = []
    for h in reversed(st.session_state.history[-10:]):
        st.caption(h)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("🔍 Generated SQL", expanded=False):
                st.code(msg["sql"], language="sql")
        if msg.get("df") is not None:
            st.dataframe(msg["df"], use_container_width=True)
            numeric_cols = msg["df"].select_dtypes(include="number").columns
            if len(numeric_cols) >= 1 and 1 < len(msg["df"]) <= 30:
                try:
                    st.bar_chart(msg["df"].set_index(msg["df"].columns[0])[numeric_cols])
                except Exception:
                    pass

pending = st.session_state.pop("pending_question", None)
prompt = st.chat_input("Ask a question about Olympic history...") or pending

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.history.append(prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = ask_cortex_analyst(prompt)
                content_blocks = response["message"]["content"]

                text_parts = [b["text"] for b in content_blocks if b["type"] == "text"]
                sql_parts = [b["statement"] for b in content_blocks if b["type"] == "sql"]

                answer_text = " ".join(text_parts) if text_parts else "Here's what I found:"
                st.markdown(answer_text)

                sql = sql_parts[0] if sql_parts else None
                df = None

                if sql:
                    with st.expander("🔍 Generated SQL", expanded=False):
                        st.code(sql, language="sql")
                    df = run_sql(sql)
                    st.dataframe(df, use_container_width=True)

                    numeric_cols = df.select_dtypes(include="number").columns
                    if len(numeric_cols) >= 1 and 1 < len(df) <= 30:
                        try:
                            st.bar_chart(df.set_index(df.columns[0])[numeric_cols])
                        except Exception:
                            pass

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer_text,
                    "sql": sql,
                    "df": df,
                })

            except Exception as e:
                error_msg = f"Something went wrong: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})