from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(override=True)

from .ingestion import ingest_all_docs
from .vector_store import create_and_save_index, semantic_search
from .chatbot import generate_answer

app = FastAPI(
    title="Asistente de Soporte Técnico API",
    description="API RAG para responder preguntas basadas en documentación técnica.",
    version="1.0.0"
)

DOCS_FOLDER = "docs"

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    context_sources: list

@app.post("/ingest")
def ingest_documents():
    """Lee todos los documentos en /docs, los procesa, y guarda en FAISS."""
    try:
        chunks = ingest_all_docs(DOCS_FOLDER)
        if not chunks:
            return {"message": "No se encontraron documentos o no se generaron fragmentos."}
            
        create_and_save_index(chunks)
        return {"message": f"Ingesta completada con éxito. {len(chunks)} fragmentos indexados."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error durante la ingesta: {str(e)}")

@app.post("/query", response_model=QueryResponse)
def query_assistant(request: QueryRequest):
    """Recibe una pregunta, busca el contexto y genera una respuesta."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")
        
    try:
        context_docs = semantic_search(question, k=3)
        sources = list(set([doc.metadata.get("source", "Desconocida") for doc in context_docs]))
        answer = generate_answer(question, context_docs)
        
        return QueryResponse(answer=answer, context_sources=sources)
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando la consulta: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

