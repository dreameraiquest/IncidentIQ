import os
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

_vectorstore = None

def get_vectorstore():
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore
    
    kb_path = os.getenv("workDir", "src/rag") + "/knowledge_base/runbooks"
    if not os.path.exists(kb_path):
        os.makedirs(kb_path, exist_ok=True)
        # Create a default runbook if none exists
        with open(f"{kb_path}/default.txt", "w") as f:
            f.write("GENERAL_TRIAGE: Check logs. Restart service. Scale resources.")

    try:
        # Switch to LOCAL embeddings to avoid 401 errors
        print("💡 Initializing Local HuggingFace Embeddings (all-MiniLM-L6-v2)...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        loader = DirectoryLoader(kb_path, glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        if not documents:
            return None
            
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        _vectorstore = FAISS.from_documents(chunks, embeddings)
        print("✅ FAISS Vector Index ready.")
        return _vectorstore
    except Exception as e:
        print(f"⚠️ RAG Initialization Error: {e}. Falling back to lexical mode.")
        return None

def retrieve_rag_context(category: str, signature: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Step 5: RAG Library - Retrieves context from local runbooks using FAISS vector search.
    """
    vs = get_vectorstore()
    if vs:
        try:
            query = f"{category} {signature}"
            docs = vs.similarity_search(query, k=top_k)
            return [{"title": d.metadata.get("source", "Runbook"), "content": d.page_content} for d in docs]
        except Exception as e:
            print(f"⚠️ RAG Retrieval Error: {e}")
    
    # Lexical Fallback
    return [{"title": f"SOP: {category} (Fallback)", "content": f"Manual triage required for {signature}."}]
