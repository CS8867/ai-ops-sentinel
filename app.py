import os
import asyncio
import re
from typing import TypedDict, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# --- 1. DEFINE THE STATE ---

class GraphState(TypedDict):
    csv_content: str
    log_content: str
    decision: str
    error_chunk: str
    context_text: str
    analysis_report: str
    target_file: str
    generated_fix: str
    github_result: str


# --- 2. DEFINE THE NODES ---

def triage_node(state: GraphState):
    """Analyzes performance metrics to classify system health as INCIDENT or HEALTHY."""
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    triage_prompt = PromptTemplate.from_template(
        "Analyze these metrics: {metrics}. Rules: IF Failures > 0 OR Failures/s > 0 THEN 'INCIDENT' ELSE 'HEALTHY'. Output only the word."
    )
    chain = triage_prompt | llm | StrOutputParser()
    decision = chain.invoke({"metrics": state["csv_content"]})
    return {"decision": decision.strip()}


def log_extraction_node(state: GraphState):
    """Extracts the relevant stack trace or error from application logs."""
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    log_parser_prompt = PromptTemplate.from_template(
        "Review these logs and extract the specific stack trace/error causing the crash. Logs: {logs}"
    )
    chain = log_parser_prompt | llm | StrOutputParser()
    log_tail = "\n".join(state["log_content"].splitlines()[-100:])
    error_chunk = chain.invoke({"logs": log_tail})
    return {"error_chunk": error_chunk}


def rca_fixer_node(state: GraphState):
    """Retrieves relevant code from the vector store, performs root cause analysis,
    and generates a corrected version of the faulty file."""
    llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    docs = retriever.invoke(state["error_chunk"])
    context_text = "\n\n".join(doc.page_content for doc in docs)
    raw_path = docs[0].metadata.get("source") or docs[0].metadata.get("file_path") if docs else "Unknown"
    # Strip the local app directory so GitHub receives a repo-relative path (e.g. "services.py")
    try:
        found_path = os.path.relpath(raw_path, "./test-python-code").replace("\\", "/")
    except (ValueError, TypeError):
        found_path = os.path.basename(raw_path)

    rca_template = """
    You are a Senior Python SRE.
    1. Analyze the Error: {question}
    2. Read the Code: {context}
    3. Explain the Root Cause.
    4. Provide the COMPLETE corrected file content.
    IMPORTANT: Wrap code inside <FIX_CODE> tags.
    """
    prompt = PromptTemplate.from_template(rca_template)
    chain = prompt | llm | StrOutputParser()
    report = chain.invoke({"question": state["error_chunk"], "context": context_text})

    code_match = re.search(r"<FIX_CODE>(.*?)</FIX_CODE>", report, re.DOTALL)
    generated_fix = code_match.group(1).strip() if code_match else None

    return {
        "analysis_report": report,
        "generated_fix": generated_fix,
        "target_file": found_path
    }


async def github_action_node(state: GraphState):
    """Pushes the generated fix to GitHub via the MCP GitHub server."""
    if not state["generated_fix"]:
        return {"github_result": "No fix generated to push."}

    server_params = StdioServerParameters(
        command="npx.cmd",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PAT")}
    )

    owner = os.getenv("GITHUB_OWNER", "CS8867")
    repo = os.getenv("GITHUB_REPO", "sentinel-python-target")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool("create_or_update_file", {
                    "owner": owner,
                    "repo": repo,
                    "path": state["target_file"],
                    "content": state["generated_fix"],
                    "message": f"AI-SRE: Automated fix for {state['target_file']}",
                    "branch": "ai-remediation"
                })
                return {"github_result": str(result)}
    except Exception as e:
        return {"github_result": f"GitHub push failed: {e}"}


# --- 3. BUILD THE GRAPH ---

def decide_to_analyze(state: GraphState):
    """Conditional edge: route to log extraction on INCIDENT, otherwise end."""
    if "INCIDENT" in state["decision"]:
        return "extract_logs"
    return "end"


workflow = StateGraph(GraphState)

workflow.add_node("triage", triage_node)
workflow.add_node("extract_logs", log_extraction_node)
workflow.add_node("rca_fixer", rca_fixer_node)
workflow.add_node("github_push", github_action_node)

workflow.set_entry_point("triage")

workflow.add_conditional_edges(
    "triage",
    decide_to_analyze,
    {
        "extract_logs": "extract_logs",
        "end": END
    }
)

workflow.add_edge("extract_logs", "rca_fixer")
workflow.add_edge("rca_fixer", "github_push")
workflow.add_edge("github_push", END)

app = workflow.compile()


# --- 4. INTEGRATION ---

def run_analysis_with_graph(csv_text, log_text):
    """Entry point: runs the full RCA pipeline and updates Streamlit session state."""
    inputs = {
        "csv_content": csv_text,
        "log_content": log_text,
        "decision": "",
        "error_chunk": "",
        "context_text": "",
        "analysis_report": "",
        "target_file": "",
        "generated_fix": "",
        "github_result": ""
    }

    return asyncio.run(app.ainvoke(inputs))