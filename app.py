# import streamlit as st
# import os
# import re
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_core.prompts import PromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.output_parsers import StrOutputParser
# import dotenv

# dotenv.load_dotenv()

# st.set_page_config(page_title="AI Ops Sentinel", layout="wide") # Just set the page title and layout. UI stuff, not important. But knowing what layout=wide does might help later?
# st.title("🛡️ AI Ops Sentinel Dashboard") # Just set the title

# # print(f"api_key: {os.getenv('GOOGLE_API_KEY')}")  # Debugging line to check if the API key is being set correctly.

# with st.sidebar:  # Renders the sidebar for the app. All the components inside this block will appear in the sidebar. If you need anythin else to show up in the sidebar, put it inside this block. If you need something to show up in the sidebar once something happens, you will have to create another with block and add it in that if else logic you will create later.
#     st.header("Configuration")
#     # api_key = st.text_input("Google API Key", type="password")
#     env_api_key = os.getenv("GOOGLE_API_KEY", "")
#     api_key = st.text_input("Google API Key", type="password", value=env_api_key)
#     if api_key: os.environ["GOOGLE_API_KEY"] = api_key
    
#      # Debugging line to check if the API key is being set correctly.
    
#     st.divider()
#     uploaded_csv = st.file_uploader("Upload Metrics (CSV)", type=["csv"])
#     uploaded_log = st.file_uploader("Upload Application Logs", type=["log", "txt"])


# # Session state is basically a dictionary that persists till the user refreshes/closes the tab, or till the server restarts. Maybe add a way to persist the generated fix across refreshes later? But that's probably if you want to give each user their own accounts.
# if "generated_fix" not in st.session_state:
#     st.session_state.generated_fix = None
# if "target_file" not in st.session_state:
#     st.session_state.target_file = None


# # def run_analysis(csv_content, log_content):
# #     if "GOOGLE_API_KEY" not in os.environ:
# #         st.error("Please enter API Key.")
# #         return

# #     # Setup
# #     llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
# #     embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# #     vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
# #     retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# #     # 1. Triage
# #     with st.status("🕵️ Triage Agent Working...", expanded=True) as status:
# #         triage_prompt = PromptTemplate.from_template(
# #             "Analyze these metrics: {metrics}. Rules: IF Failures > 0 OR Failures/s > 0 THEN 'INCIDENT' ELSE 'HEALTHY'. Output only the word."
# #         )
# #         triage_chain = triage_prompt | llm | StrOutputParser()
# #         decision = triage_chain.invoke({"metrics": csv_content})
        
# #         if "INCIDENT" not in decision:
# #             status.update(label="✅ System Healthy", state="complete")
# #             st.success("No issues detected.")
# #             return

# #         status.update(label="🚨 Incident Detected!", state="error")
        
# #         # 2. RCA (Fixer)
# #         st.write("🔍 Identifying Root Cause...")
        
# #         # Find Error in Logs
# #         error_chunk = ""
# #         lines = log_content.splitlines()
# #         for i, line in enumerate(lines):
# #             if "ERROR" in line:
# #                 error_chunk = "\n".join(lines[i:i+20]) 
# #                 break
        
# #         # RAG Pipeline setup
# #         rca_template = """
# #         You are a Senior Java SRE. 
# #         1. Analyze the Error: {question}
# #         2. Read the Code: {context}
# #         3. Explain the Root Cause.
# #         4. Provide the COMPLETE corrected file content for the specific Java file that crashed.
        
# #         IMPORTANT: Wrap the full corrected Java code inside <FIX_CODE> and </FIX_CODE> tags.
# #         """
# #         prompt = PromptTemplate.from_template(rca_template)

# #         # --- DEBUGGING FUNCTION ---
# #         def format_docs(docs):
# #             if docs:
# #                 # DEBUG: Print all metadata keys to the UI
# #                 st.write("--- DEBUG: RETRIEVED DOC METADATA ---")
# #                 st.json(docs[0].metadata) 
                
# #                 # Try to find the source
# #                 # GenericLoader often uses 'source', but let's be safe
# #                 source_path = docs[0].metadata.get("source") or docs[0].metadata.get("file_path")
                
# #                 st.session_state.target_file = source_path
                
# #             return "\n\n".join(doc.page_content for doc in docs)
# #         # --------------------------

# #         rag_chain = (
# #             {"context": retriever | format_docs, "question": RunnablePassthrough()}
# #             | prompt
# #             | llm
# #             | StrOutputParser()
# #         )
        
# #         report = rag_chain.invoke(error_chunk)
        
# #         # Extract Code
# #         code_match = re.search(r"<FIX_CODE>(.*?)</FIX_CODE>", report, re.DOTALL)
# #         if code_match:
# #             st.session_state.generated_fix = code_match.group(1).strip()
        
# #         return report


# def run_analysis(csv_content, log_content):
#     # Check if the API key is set.
#     if "GOOGLE_API_KEY" not in os.environ:
#         st.error("Please enter API Key.")
#         return

    
#     # Get the llm. I need to experiment with the temperature later.
#     llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    
#     # Get the embeddings. What are embeddings? They are numerical vectors that represent text, and allow us to measure similarity between texts. Different models create different embeddings. An ideal project will have run experiments across different best-fit models to find the best one for their codebase. Need to figure out the exact process for this.
#     # Got it. We need to look at sites such as huggingface MTEB, hugging face model cards, or other academic papers that benchmark embedding models on code similarity tasks. We then will have to perhaps understand the benchmarks in the first place. Meaning, what does every metric represent? And why does this metric work? Why Recall for example? Why not Precision? Or F1? Once we understand that, we can then run our own benchmarks on our own codebase, and see which embedding model performs the best. This is important because different codebases have different characteristics, and a model that works well for one codebase may not work well for another.
#     embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

#     # Load the vector DB. The vectorDB will store the embeddings provided by the model we imported.
#     vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

#     # Initialize the retriever. The retriever is likely the object that provides an interface to query the vector DB.
#     # search_kwargs is seriously important. It tells the retriever how many results to fetch. k=3 means 3 results. If you set k=1, it will only fetch 1 result. If you set k=5, it will fetch 5 results. This is important because fetching too few results may miss relevant context, while fetching too many may introduce noise.
#     # This is basically the precision/recall tradeoff. If we increase k, we increase recall, which may increase the number of noisy results. If we decrease k, we may increase precision, but we may miss relevant context. The correct idea is to determine the highest number of noisy documents we can tolerate. That will fix our k value (if we assume current precision is constant). We then find ways to increase precision (better embeddings, better vector DB, better retriever algorithms etc) for this k value. One question is, is "number of correct documents retrieved"/"number of noisy documents" the correct way to look at it. Will the person setting the requirements give us this metric (which would almost equate spoon feeding). The end goal is to increase the accuracy of the system. The process starts from determining which metric we need to measure, and then optimizing for that metric. Will this require learning statistics? This will certainly require reviewing a lot of academic papers on information retrieval (case studies on what metric worked for what scenario).
#     retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

#     # 1. Triage Agent
#     # The st.status with block is likely another streamlit component that shows a status message. This renders a status panel till the code in the block runs. If you want to change the content of the status panel, use status.update. If you just want to append some content to the status panel, use st.write inside the block.
#     with st.status("🕵️ Triage Agent Working...", expanded=True) as status:
#         # Create the prompt template for triage. This prompt template will be used to create the prompt for the LLM.
#         triage_prompt = PromptTemplate.from_template(
#             "Analyze these metrics: {metrics}. Rules: IF Failures > 0 OR Failures/s > 0 THEN 'INCIDENT' ELSE 'HEALTHY'. Output only the word."
#         )
#         # Create the triage chain. The prompt is already formatted by the PromptTemplate and stored in triage_prompt. The triage_prompt is further piped into the llm, and then into the StrOutputParser which extracts the string output from the llm response.
#         triage_chain = triage_prompt | llm | StrOutputParser()
#         # Pass the csv content into the triage chain and get the decision. In our case, we pass the csv content in the "metrics" variable, which is baked into the prompt template above. The prompt clearly shows what the llm is expected to do.
#         decision = triage_chain.invoke({"metrics": csv_content})
        
#         # The llm has made a decision based on the metrics provided. If the decision does not contain "INCIDENT", we update the status panel to show that the system is healthy, and return from the function.
#         if "INCIDENT" not in decision:
#             status.update(label="✅ System Healthy", state="complete")
#             st.success("No issues detected.")
#             return

#         # If INCIDENT is detected, we update the status panel to show that an incident has been detected.
#         status.update(label="🚨 Incident Detected!", state="error")
        
#         # 2. RCA Agent (The Fixer)
#         # Since we detected an incident, we now proceed to find the root cause and fix it.
#         st.write("🔍 Identifying Root Cause...")
        
#         # Step A: Find Error in Logs
#         # Parse the log content. We look for the first occurrence of "ERROR" in the logs, and extract a chunk of 20 lines starting from that line. This chunk will be used to identify the error.
#         error_chunk = ""
#         lines = log_content.splitlines()
#         for i, line in enumerate(lines):
#             if "ERROR" in line:
#                 error_chunk = "\n".join(lines[i:i+20]) 
#                 break
        
#         # If no error is found, we return None. This will be a problem later because the UI will not show any report. We need to handle this case better later. It may be that the errors are caused by an error in the automation script itself. This needs to be made clear to the user.
#         if not error_chunk:
#             st.error("No ERROR found in logs.")
#             return None

#         # Step B: RETRIEVE (Explicitly fetch docs first)
#         st.write("📚 Retrieving Context from Vector DB...")
#         # Find the docs most similar to the error chunk from the vector DB. Basically, this should fetch the code snippets where the error log has been declared in a print statement.
#         docs = retriever.invoke(error_chunk)
        

#         if docs:
#             # This snippet is just for debugging purposes. It shows the number of documents retrieved, and the metadata of the first document. This is useful to understand what metadata keys are available, so we can later extract the file path from the metadata.
#             st.info(f"Retrieved {len(docs)} documents.")
#             st.write("--- DEBUG METADATA ---")
#             st.json(docs[0].metadata) # <--- THIS will show us the key name!
            
#             # Smartly look for the path
#             # It usually hides in 'source' or 'file_path'
#             found_path = docs[0].metadata.get("source") or docs[0].metadata.get("file_path")
#             st.session_state.target_file = found_path
            
#             context_text = "\n\n".join(doc.page_content for doc in docs)
#         else:
#             st.warning("No relevant source code found.")
#             context_text = ""
#         # ---------------------------------------------------------------

#         # Create the prompt for RCA. Possible interview question. How would I improve this prompt to reduce hallucinations? Maybe add more constraints? Maybe add more steps to the reasoning process?
#         # The end result is a report as well as the corrected code wrapped in <FIX_CODE> tags.
#         rca_template = """
#         You are a Senior Java SRE. 
#         1. Analyze the Error: {question}
#         2. Read the Code: {context}
#         3. Explain the Root Cause.
#         4. Provide the COMPLETE corrected file content for the specific Java file that crashed.
        
#         IMPORTANT: Wrap the full corrected Java code inside <FIX_CODE> and </FIX_CODE> tags.
#         """
#         prompt = PromptTemplate.from_template(rca_template)
        
#         # Simple chain: Prompt -> LLM -> Parser
#         chain = prompt | llm | StrOutputParser()
#         report = chain.invoke({"question": error_chunk, "context": context_text})

#         print(report, flush=True)  # Debugging line to see the report in the server logs.
        
#         # Extract Code
#         code_match = re.search(r"<FIX_CODE>(.*?)</FIX_CODE>", report, re.DOTALL)
#         if code_match:
#             # print("Entered code_match block", flush=True)  # Debugging line to confirm code extraction.
#             st.session_state.generated_fix = code_match.group(1).strip()
#             # print("st.session_state.generated_fix:", st.session_state.generated_fix, flush=True)  # Debugging line to see the extracted code.
        
#         return report


# if st.button("🚀 Run AI Analysis", type="primary"):
#     if uploaded_csv and uploaded_log:
#         csv_text = uploaded_csv.getvalue().decode("utf-8")
#         log_text = uploaded_log.getvalue().decode("utf-8")
#         report_text = run_analysis(csv_text, log_text)

#         # print("report_text:", report_text, flush=True)  # Debugging line to see the report text.
        
#         if report_text:
#             st.markdown("### 📝 Analysis Report")
#             clean_report = report_text.replace("<FIX_CODE>", "```java").replace("</FIX_CODE>", "```")
#             st.markdown(clean_report)


# if st.session_state.generated_fix:
#     # If we found a fix, show the remediation section
#     st.divider()
#     st.subheader("🛠️ Automated Remediation")
    
#     # This is dividing the UI into 2 columns, with the first column being 3 times the size of the second column?
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         st.info(f"Target File Detected: `{st.session_state.target_file}`")
#         with st.expander("Preview Generated Code"):
#             st.code(st.session_state.generated_fix, language='java')
            
#     with col2:
#         # This is just overwriting the file (the path to which we know from earlier) with the fixed code.
#         if st.button("💾 Apply Fix to File"):
#             target_path = st.session_state.target_file
#             if target_path and os.path.exists(target_path):
#                 try:
#                     with open(target_path, "w", encoding="utf-8") as f:
#                         f.write(st.session_state.generated_fix)
#                     st.success("✅ Fix applied successfully!")
#                     st.session_state.generated_fix = None
#                 except Exception as e:
#                     st.error(f"Error writing file: {e}")
#             else:
#                 st.error(f"❌ File not found at path: {target_path}")

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
st.title("🛡️ AI Ops Sentinel Dashboard")

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
    with st.status("🕵️ Triage Agent Working...", expanded=True) as status:
        st.write("DEBUG: Analyzing Metrics for Anomalies...")
        
        triage_prompt = PromptTemplate.from_template(
            "Analyze these metrics: {metrics}. Rules: IF Failures > 0 OR Failures/s > 0 THEN 'INCIDENT' ELSE 'HEALTHY'. Output only the word."
        )
        triage_chain = triage_prompt | llm | StrOutputParser()
        decision = triage_chain.invoke({"metrics": csv_content})
        
        st.write(f"DEBUG: Decision -> **{decision}**")

        if "INCIDENT" not in decision:
            status.update(label="✅ System Healthy", state="complete")
            st.success("No issues detected.")
            return None

        status.update(label="🚨 Incident Detected!", state="error")
        
        # 3. RCA Agent (The Fixer)
        st.write("🔍 Identifying Root Cause...")
        
        # Step A: Find Error in Logs
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
        st.write("📚 Retrieving Context from Vector DB...")
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
if st.button("🚀 Run AI Analysis", type="primary"):
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
    st.markdown("### 📝 Analysis Report")
    clean_report = st.session_state.analysis_report.replace("<FIX_CODE>", "```java").replace("</FIX_CODE>", "```")
    st.markdown(clean_report)

# 3. Display Remediation (Persistent)
if st.session_state.generated_fix:
    st.divider()
    st.subheader("🛠️ Automated Remediation")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"Target File Detected: `{st.session_state.target_file}`")
        with st.expander("Preview Generated Code"):
            st.code(st.session_state.generated_fix, language='java')
            
    with col2:
        if st.button("💾 Apply Fix to File"):
            target_path = st.session_state.target_file
            if target_path and os.path.exists(target_path):
                try:
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(st.session_state.generated_fix)
                    st.success("✅ Fix applied successfully!")
                    # Optional: reset fix state if you want to force re-analysis
                    # st.session_state.generated_fix = None 
                except Exception as e:
                    st.error(f"Error writing file: {e}")
            else:
                st.error(f"❌ File not found at path: {target_path}")