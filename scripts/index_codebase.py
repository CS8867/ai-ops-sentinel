import os
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Initialize the repo_path to find the files to index
repo_path = "./spring-petclinic"

if not os.path.exists(repo_path):
    print(f"Error: Repository not found at {repo_path}")
    exit()

print("1. Loading Java Files (This may take a minute)...")
# We are using an AST Parser instead of a text parser. A text parser will dumbly chunk code by characters like '{' or '\n' which may break the function itself. An AST-parser is likely trained (is it actually trained?) to understand code structure and keep functions/classes whole.
# I needed to understand where the parsing is happening exactly. Is it happening here, or later during the RecursiveCharacterTextSplitter. Apparently, the AST is traversed here itself. The result is, that the loader contains documents that correspond to whole functions or classes, not one giant file itself. Basically, each document now corresponds to a syntactic unit, for the specific language which is Java.
loader = GenericLoader.from_filesystem(
    repo_path,
    glob="**/*.java",
    suffixes=[".java"],
    parser=LanguageParser(language=Language.JAVA, parser_threshold=500)
)
documents = loader.load()
print(f"   Loaded {len(documents)} Java files.")


# We already have the docs, each of which likely corresponds to a function or a class. Honestly, most of our work is already done at this point. The problem is going to arise when the character count for any individual document exceeds 2000. That's where we need to chunk it further, and intelligently. Thus we use a RecursiveCharacterTextSplitter that is aware of Java syntax (we pass language = language.JAVA). This splitter will try to split at logical boundaries like method ends, class ends, etc. rather than just splitting at arbitrary character counts.
print("2. Splitting Code intelligently...")
java_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.JAVA, 
    chunk_size=2000, 
    chunk_overlap=200
)
texts = java_splitter.split_documents(documents)
print(f"   Created {len(texts)} code chunks.")

# 3. Embed & Store
# We have our splitted chunks. Now we pass them to the embedding model and store them to the Vector DB.
print("3. Creating Vector Database...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma.from_documents(texts, embeddings, persist_directory="./chroma_db")

print("Success! Knowledge Base Rebuilt with Java Awareness.")