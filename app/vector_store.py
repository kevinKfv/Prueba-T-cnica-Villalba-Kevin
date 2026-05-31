import os
from typing import List, Dict
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

VECTORSTORE_PATH = "faiss_index"

def get_embeddings():
    """Retorna la instancia de Embeddings locales de HuggingFace."""
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def create_and_save_index(chunks: List[Dict]):
    """Crea un índice FAISS a partir de los chunks y lo guarda en disco."""
    if not chunks:
        raise ValueError("No hay fragmentos para indexar.")
        
    embeddings = get_embeddings()
    documents = [Document(page_content=chunk["page_content"], metadata=chunk["metadata"]) for chunk in chunks]
    
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(VECTORSTORE_PATH)
    return True

def load_index() -> FAISS:
    """Carga el índice FAISS desde el disco."""
    if not os.path.exists(VECTORSTORE_PATH):
        return None
    embeddings = get_embeddings()
    return FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)

def semantic_search(query: str, k: int = 3) -> List[Document]:
    """Busca en el índice vectorial los fragmentos más similares a la query."""
    vectorstore = load_index()
    if not vectorstore:
        raise RuntimeError("El índice vectorial no existe. Ejecuta la ingesta de documentos primero.")
    
    results = vectorstore.similarity_search(query, k=k)
    return results
