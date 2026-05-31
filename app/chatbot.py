import os
from openai import OpenAI
from typing import List
from langchain_core.documents import Document

def generate_answer(query: str, context_docs: List[Document]) -> str:
    """Genera una respuesta contextual utilizando OpenAI."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY no configurada.")
        
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    
    context_text = "\n\n".join([f"Fuente ({doc.metadata.get('source', 'Desconocida')}):\n{doc.page_content}" for doc in context_docs])
    
    system_prompt = (
        "Eres un asistente de soporte técnico experto. Tu tarea es responder preguntas de los usuarios "
        "basándote ÚNICAMENTE en la documentación proporcionada en el contexto.\n\n"
        "Reglas estrictas:\n"
        "1. Usa solo la información del contexto proporcionado.\n"
        "2. Si la respuesta a la pregunta NO se encuentra en el contexto, DEBES responder explícitamente: "
        "'Lo siento, no tengo información en mi documentación sobre eso.' No inventes ni adivines.\n"
        "3. Sé claro y conciso."
    )
    
    user_prompt = f"Contexto:\n{context_text}\n\nPregunta del usuario: {query}"
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0
    )
    
    return response.choices[0].message.content
