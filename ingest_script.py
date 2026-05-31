import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append('.')
from app.ingestion import ingest_all_docs
from app.vector_store import create_and_save_index

try:
    chunks = ingest_all_docs('docs')
    if chunks:
        create_and_save_index(chunks)
        print(f'Exito: {len(chunks)} chunks indexados y base de datos guardada en faiss_index/')
    else:
        print('No se generaron chunks.')
except Exception as e:
    import traceback
    traceback.print_exc()
