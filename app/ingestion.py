import os
import json
import re
from typing import List, Dict
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text: str) -> str:
    """Limpia el texto eliminando ruido y caracteres especiales innecesarios."""
    if not text:
        return ""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.,;:!?\-\(\)\[\]"\'áéíóúÁÉÍÓÚñÑüÜ]', '', text)
    return text.strip()

def read_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_md(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def read_json(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return json.dumps(data, indent=2, ensure_ascii=False)

def read_pdf(file_path: str) -> str:
    text = ""
    reader = PdfReader(file_path)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def process_document(file_path: str) -> str:
    """Lee un documento dependiendo de su extensión y retorna el texto limpio."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    text = ""
    try:
        if ext == '.txt':
            text = read_txt(file_path)
        elif ext == '.md':
            text = read_md(file_path)
        elif ext == '.json':
            text = read_json(file_path)
        elif ext == '.pdf':
            text = read_pdf(file_path)
        else:
            print(f"Formato no soportado: {ext}")
            return ""
        
        return clean_text(text)
    except Exception as e:
        print(f"Error procesando {file_path}: {e}")
        return ""

def chunk_text(text: str, source: str) -> List[Dict]:
    """Divide el texto en fragmentos (chunks) utilizables."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    return [{"page_content": chunk, "metadata": {"source": source}} for chunk in chunks]

def ingest_all_docs(docs_folder: str) -> List[Dict]:
    """Procesa todos los documentos de la carpeta y devuelve los chunks."""
    all_chunks = []
    if not os.path.exists(docs_folder):
        return all_chunks
        
    for filename in os.listdir(docs_folder):
        file_path = os.path.join(docs_folder, filename)
        if os.path.isfile(file_path):
            text = process_document(file_path)
            if text:
                chunks = chunk_text(text, source=filename)
                all_chunks.extend(chunks)
                
    return all_chunks
