import streamlit as st
import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Page Setup
st.set_page_config(page_title="AI Ops Sentinel", layout="wide")
st.title("AI Ops Sentinel Dashboard")

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.header("Configuration")
    
    # Pre-fill API Key from .env if available
    env_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input("Google API Key", type="password", value=env_api_key)
    
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.divider()
    uploaded_csv = st.file_uploader("Upload Metrics (CSV)", type=["csv"])
    uploaded_log = st.file_uploader("Upload Application Logs", type=["log", "txt"])

# --- SESSION STATE INITIALIZATION ---
# This is crucial for persistence. We initialize variables once so they survive reruns.
if "generated_fix" not in st.session_state:
    st.session_state.generated_fix = None
if "target_file" not in st.session_state:
    st.session_state.target_file = None
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = None


# --- MAIN ANALYSIS FUNCTION ---
def run_analysis(csv_content, log_content):
    if "GOOGLE_API_KEY" not in os.environ:
        st.error("Please enter API Key.")
        return None

    # 1. Setup Models & DB
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 2. Triage Agent
    with st.status("Triage Agent Working...", expanded=True) as status:
        st.write("DEBUG: Analyzing Metrics for Anomalies...")
        
        # We are basically saying here that the Failures > 0 is our signal, which can leak a LOT of false positives. Look at the prompt. This may require some LLM finetuning. Light weight solutions may be using Auto-encoders, or LSTMs, or RNNs, or Logistic Regression (Depending on how much compute we have)
        triage_prompt = PromptTemplate.from_template(
            "Analyze these metrics: {metrics}. Rules: IF Failures > 0 OR Failures/s > 0 THEN 'INCIDENT' ELSE 'HEALTHY'. Output only the word."
        )
        triage_chain = triage_prompt | llm | StrOutputParser()
        decision = triage_chain.invoke({"metrics": csv_content})
        
        st.write(f"DEBUG: Decision -> **{decision}**")

        # Incident detection is very rudimentary here. We need to come up with ways to detect false postives like I mentioned above. But this is low priority right now.
        if "INCIDENT" not in decision:
            status.update(label="System Healthy", state="complete")
            st.success("No issues detected.")
            return None

        status.update(label="Incident Detected!", state="error")
        
        # 3. RCA Agent (The Fixer)
        st.write("Identifying Root Cause...")
        
        # Step A: Find Error in Logs
        # Probably better to use LLM capability here, since the logs can be complex. Simply scanning for "ERROR" may not be sufficient.
        error_chunk = ""
        lines = log_content.splitlines()
        for i, line in enumerate(lines):
            if "ERROR" in line:
                error_chunk = "\n".join(lines[i:i+20]) 
                break
        
        if not error_chunk:
            st.error("No 'ERROR' keyword found in logs.")
            return None

        st.write(f"DEBUG: Found Error Chunk ({len(error_chunk)} chars)")

        # Step B: Retrieve Context
        st.write("Retrieving Context from Vector DB...")
        docs = retriever.invoke(error_chunk)
        
        if docs:
            st.info(f"Retrieved {len(docs)} documents.")
            st.write("--- DEBUG: METADATA ---")
            st.json(docs[0].metadata) # Visual confirmation of what was found
            
            # Extract file path securely
            found_path = docs[0].metadata.get("source") or docs[0].metadata.get("file_path")
            st.session_state.target_file = found_path
            
            context_text = "\n\n".join(doc.page_content for doc in docs)
        else:
            st.warning("No relevant source code found.")
            context_text = ""

        # Step C: Generate Report
        rca_template = """
        You are a Senior Java SRE. 
        1. Analyze the Error: {question}
        2. Read the Code: {context}
        3. Explain the Root Cause.
        4. Provide the COMPLETE corrected file content for the specific Java file that crashed.
        
        IMPORTANT: Wrap the full corrected Java code inside <FIX_CODE> and </FIX_CODE> tags.
        """
        prompt = PromptTemplate.from_template(rca_template)
        chain = prompt | llm | StrOutputParser()
        
        report = chain.invoke({"question": error_chunk, "context": context_text})
        
        # Step D: Extract Fix Code
        code_match = re.search(r"<FIX_CODE>(.*?)</FIX_CODE>", report, re.DOTALL)
        if code_match:
            st.session_state.generated_fix = code_match.group(1).strip()
        
        return report


# --- UI INTERACTION LOGIC ---

# 1. The Trigger Button
if st.button("Run AI Analysis", type="primary"):
    if uploaded_csv and uploaded_log:
        csv_text = uploaded_csv.getvalue().decode("utf-8")
        log_text = uploaded_log.getvalue().decode("utf-8")
        
        # Run analysis and SAVE result to session state
        report_text = run_analysis(csv_text, log_text)
        if report_text:
            st.session_state.analysis_report = report_text
    else:
        st.error("Please upload both CSV and Log files.")

# 2. Display Report (Persistent)
# We check session_state, not the button variable, so this persists after refresh/clicks
if st.session_state.analysis_report:
    st.markdown("### Analysis Report")
    clean_report = st.session_state.analysis_report.replace("<FIX_CODE>", "```java").replace("</FIX_CODE>", "```")
    st.markdown(clean_report)

# 3. Display Remediation (Persistent)
if st.session_state.generated_fix:
    st.divider()
    st.subheader("Automated Remediation")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Target File Detected: `{st.session_state.target_file}`")
        with st.expander("Preview Generated Code"):
            st.code(st.session_state.generated_fix, language='java')
            
    with col2:
        if st.button("Apply Fix to File"):
            target_path = st.session_state.target_file
            if target_path and os.path.exists(target_path):
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(st.session_state.generated_fix)
                    st.success("Fix applied successfully!")
                    # Optional: reset fix state if you want to force re-analysis
                    # st.session_state.generated_fix = None 
                except Exception as e:
                    st.error(f"Error writing file: {e}")
            else:
                st.error(f"File not found at path: {target_path}")