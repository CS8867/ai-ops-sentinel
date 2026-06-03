import os
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Path to the repository to index
repo_path = "./test-python-code"

if not os.path.exists(repo_path):
    print(f"Error: Repository not found at {repo_path}")
    exit()

# Step 1: Load Python files using an AST-aware parser.
# Unlike naive text-based chunking, the AST parser uses a formal grammar (via tree-sitter)
# to deterministically parse code structure, keeping syntactic units like classes and
# functions atomic rather than splitting them at arbitrary character boundaries.
print("1. Loading Python files...")
loader = GenericLoader.from_filesystem(
    repo_path,
    glob="**/*.py",
    suffixes=[".py"],
    parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
)
documents = loader.load()
print(f"   Loaded {len(documents)} documents.")

# Step 2: Split large documents further using a Python-aware recursive splitter.
# Documents that exceed the chunk_size are split at logical boundaries (e.g., function/class ends)
# rather than at arbitrary character counts.
print("2. Splitting code into chunks...")
python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=1500,
    chunk_overlap=150
)
texts = python_splitter.split_documents(documents)
print(f"   Created {len(texts)} code chunks.")

# Step 3: Generate embeddings and persist to ChromaDB.
print("3. Creating vector database...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma.from_documents(texts, embeddings, persist_directory="./chroma_db")

print("Success! Knowledge base built.")