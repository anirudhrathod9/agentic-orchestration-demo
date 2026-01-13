import os
import time
import streamlit as st
from openai import OpenAI

# =============================
# PAGE CONFIG
# =============================
st.set_page_config(page_title="Agentic AI Orchestration Demo", layout="wide")

# =============================
# KEYS / CLIENT
# =============================
def get_api_key() -> str | None:
    # Streamlit Cloud: set in Secrets as GROQ_API_KEY
    # Local: export GROQ_API_KEY=...
    if "GROQ_API_KEY" in st.secrets:
        return st.secrets["GROQ_API_KEY"]
    return os.getenv("GROQ_API_KEY")

API_KEY = get_api_key()
if not API_KEY:
    st.error("Missing GROQ_API_KEY. Add it in Streamlit Secrets (Cloud) or as an environment variable locally.")
    st.stop()

# Groq OpenAI-compatible endpoint
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

# =============================
# MODEL OPTIONS (UPDATED)
# =============================
MODEL_OPTIONS = [
    "llama-3.1-70b-versatile",  # best quality
    "llama-3.1-8b-instant",     # fastest
    "mixtral-8x7b-32768",       # good alternative
]

# =============================
# LLM CALL
# =============================
def call_llm(model: str, system_prompt: str, user_prompt: str, temperature: float = 0.6) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content.strip()

# =============================
# ARCHITECTURES
# =============================
def run_sequential(model: str, question: str):
    s1 = call_llm(
        model,
        "You are Agent A. Frame the core dilemma and what a 'good answer' must consider. 4-6 bullets max.",
        question,
        temperature=0.4,
    )
    s2 = call_llm(
        model,
        "You are Agent B. Using the framing, list pros and cons. Keep it crisp and balanced.",
        s1,
        temperature=0.4,
    )
    s3 = call_llm(
        model,
        "You are Agent C. Give a final decision in 3-5 lines. Reference the pros/cons and be practical.",
        s2,
        temperature=0.4,
    )
    return [
        ("Step 1 — Frame dilemma", s1),
        ("Step 2 — Pros vs Cons", s2),
        ("Final — Decision", s3),
    ]

def run_hierarchical(model: str, question: str):
    expert1 = call_llm(
        model,
        "You are Expert 1 (Domain Expert). Clarify the context, key concepts, and the core decision criteria. 5-7 bullets.",
        question,
        temperature=0.5,
    )
    expert2 = call_llm(
        model,
        "You are Expert 2 (Risks & Constraints). Identify risks, assumptions, constraints, edge cases, and failure modes. 5-7 bullets.",
        question,
        temperature=0.5,
    )
    expert3 = call_llm(
        model,
        "You are Expert 3 (Stakeholders & Impact). Consider stakeholders, incentives, fairness/ethics, and practical adoption implications. 5-7 bullets.",
        question,
        temperature=0.5,
    )

    manager = call_llm(
        model,
        "You are the Manager Agent. Synthesize the experts into ONE final recommendation (5-7 lines) + 2 key takeaways. Keep it actionable.",
        f"Question:\n{question}\n\nDomain Expert:\n{expert1}\n\nRisks & Constraints:\n{expert2}\n\nStakeholders & Impact:\n{expert3}",
        temperature=0.4,
    )

    return [
        ("Expert — Domain", expert1),
        ("Expert — Risks & Constraints", expert2),
        ("Expert — Stakeholders & Impact", expert3),
        ("Manager — Final synthesis", manager),
    ]


def run_swarm(model: str, question: str):
    a = call_llm(
        model,
        "You are Agent 1 (Enthusiast). Strongly argue YES. 3-5 lines.",
        question,
        temperature=0.7,
    )
    b = call_llm(
        model,
        "You are Agent 2 (Purist). Strongly argue NO. 3-5 lines.",
        question,
        temperature=0.7,
    )
    c = call_llm(
        model,
        "You are Agent 3 (Diplomat). Bridge both sides. 3-5 lines.",
        question,
        temperature=0.7,
    )
    d = call_llm(
        model,
        "You are Agent 4 (Pragmatist). Focus on real-world choice/market. 3-5 lines.",
        question,
        temperature=0.7,
    )

    agg = call_llm(
        model,
        "You are the Swarm Aggregator. Summarize positions in 4 bullets, then state the 'dominant pattern' in 2-3 lines. Do NOT force consensus.",
        f"Question:\n{question}\n\nEnthusiast:\n{a}\n\nPurist:\n{b}\n\nDiplomat:\n{c}\n\nPragmatist:\n{d}",
        temperature=0.4,
    )

    return [
        ("Agent 1 — Enthusiast (YES)", a),
        ("Agent 2 — Purist (NO)", b),
        ("Agent 3 — Diplomat (BOTH)", c),
        ("Agent 4 — Pragmatist (MARKET)", d),
        ("Swarm — Aggregated view", agg),
    ]

# =============================
# UI
# =============================
st.title("Agentic AI Orchestration — Live Demo")
st.caption("Same input → different coordination pattern → different outputs (Sequential • Hierarchical • Swarm)")

model = st.selectbox("Model", MODEL_OPTIONS, index=0)

preset_questions = {
    "🍍 Pineapple on pizza? (classic)": "Should pineapple go on pizza?",
    "⏰ Snooze button? (everyday decision)": "Is it okay to press snooze more than once in the morning?",
    "🏢 Return-to-office? (workplace)": "Should companies mandate 3 days per week in the office?",
    "🤖 AI in hiring? (policy)": "Should companies use AI to screen candidates in early hiring stages?",
}

c1, c2 = st.columns([2, 3])
with c1:
    preset = st.selectbox("Pick a preset", list(preset_questions.keys()))
with c2:
    allow_custom = st.toggle("Allow custom question", value=True)

if allow_custom:
    question = st.text_area("Question", value=preset_questions[preset], height=80)
else:
    question = preset_questions[preset]
    st.info(f"Using preset: {question}")

show_steps = st.toggle("Show intermediate steps", value=True)

run = st.button("Run demo", type="primary")

if run:
    col1, col2, col3 = st.columns(3)

    try:
        with st.spinner("Running agents..."):
            t0 = time.time()
            seq = run_sequential(model, question)
            hier = run_hierarchical(model, question)
            swm = run_swarm(model, question)
            t1 = time.time()

        st.success(f"Completed in {t1 - t0:.1f}s")

        def render(col, title, items):
            with col:
                st.subheader(title)
                if show_steps:
                    for k, v in items[:-1]:
                        st.markdown(f"**{k}**")
                        st.write(v)
                        st.divider()
                st.markdown("**Final output**")
                st.write(items[-1][1])

        render(col1, "Sequential", seq)
        render(col2, "Hierarchical", hier)
        render(col3, "Swarm", swm)

        st.divider()
        st.markdown("### What to say (10 seconds)")
        st.write(
            "Sequential = step-by-step refinement • Hierarchical = experts in parallel + manager synthesis • "
            "Swarm = independent viewpoints + aggregated pattern (no forced consensus)."
        )

    except Exception as e:
        st.error(f"Run failed: {e}")
        st.info("If this persists, open Streamlit → Manage app → Logs and share the last error block.")
