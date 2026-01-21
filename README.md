# AI Ops Sentinel

**AI Ops Sentinel** is an automated incident response dashboard. It uses Generative AI (RAG) to monitor system health, identify root causes from logs, and generate code fixes for Java applications (Currently tested on the spring petclinic repo).

## Features

- **Triage Agent:** Analyzes CSV system metrics to detect incidents (Healthy vs. Incident).
- **RCA Agent:** Scans application logs for errors and retrieves relevant source code from a vector database.
- **Automated Remediation:** Generates a specific code fix for the crashed file and allows one-click patching.

## Tech Stack

- **UI:** Streamlit
- **AI/LLM:** LangChain + Google Gemini (Flash)
- **Vector DB:** ChromaDB
- **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)

## Setup & Usage

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root directory:

    ```env
    GOOGLE_API_KEY=your_api_key_here
    ```

3.  **Run the Dashboard:**
    ```bash
    streamlit run app.py
    ```
