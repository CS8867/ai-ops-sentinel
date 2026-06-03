import streamlit as st
import os
import dotenv
from app import run_analysis_with_graph

dotenv.load_dotenv(override=True)

st.set_page_config(page_title="Sentinel RCA Agent", layout="wide")
st.title("Sentinel RCA Agent")
st.caption("Autonomous Root Cause Analysis powered by LangGraph + Gemini")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Configuration")

    env_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input("Google API Key", type="password", value=env_api_key)
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key

    env_pat = os.getenv("GITHUB_PAT", "")
    github_pat = st.text_input("GitHub PAT", type="password", value=env_pat)
    if github_pat:
        os.environ["GITHUB_PAT"] = github_pat

    st.divider()
    uploaded_csv = st.file_uploader("Upload Metrics (CSV)", type=["csv"])
    uploaded_log = st.file_uploader("Upload Application Logs", type=["log", "txt"])

# --- SESSION STATE ---
for key in ["decision", "analysis_report", "generated_fix", "target_file", "github_status"]:
    if key not in st.session_state:
        st.session_state[key] = None

# --- TRIGGER ---
if st.button("Run AI Analysis", type="primary"):
    if not os.environ.get("GOOGLE_API_KEY"):
        st.error("Please enter a Google API Key in the sidebar.")
    elif not uploaded_csv or not uploaded_log:
        st.error("Please upload both a CSV metrics file and a log file.")
    else:
        csv_text = uploaded_csv.getvalue().decode("utf-8")
        log_text = uploaded_log.getvalue().decode("utf-8")

        with st.spinner("Running RCA pipeline..."):
            final_state = run_analysis_with_graph(csv_text, log_text)

        st.session_state.decision = final_state.get("decision", "")
        st.session_state.analysis_report = final_state.get("analysis_report")
        st.session_state.generated_fix = final_state.get("generated_fix")
        st.session_state.target_file = final_state.get("target_file")
        st.session_state.github_status = final_state.get("github_result")

# --- RESULTS ---
if st.session_state.decision:
    if "INCIDENT" in st.session_state.decision:
        st.error("Incident detected!")
    else:
        st.success(f"System status: **{st.session_state.decision}** — No action required.")

if st.session_state.analysis_report:
    st.markdown("### Root Cause Analysis Report")
    clean_report = (
        st.session_state.analysis_report
        .replace("<FIX_CODE>", "```python")
        .replace("</FIX_CODE>", "```")
    )
    st.markdown(clean_report)

if st.session_state.generated_fix:
    st.divider()
    st.subheader("Automated Remediation")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Target file: `{st.session_state.target_file}`")
        with st.expander("Preview generated fix"):
            st.code(st.session_state.generated_fix, language="python")
    with col2:
        st.markdown("**GitHub push status:**")
        if st.session_state.github_status:
            st.success(str(st.session_state.github_status)[:300])
        else:
            st.warning("Not pushed yet.")
