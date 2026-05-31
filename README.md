# Asistente Automatizado de Soporte Técnico (RAG)

Este proyecto implementa un asistente de soporte técnico automatizado capaz de responder preguntas basándose en una base documental interna, utilizando la técnica RAG (Retrieval-Augmented Generation). 

## Arquitectura

- **Python (FastAPI)**: Encargado de la ingesta de documentos (.pdf, .txt, .md, .json), limpieza, división (chunking), generación de embeddings y búsqueda semántica utilizando FAISS y HuggingFace. También gestiona la comunicación con la API de Groq para la generación de la respuesta basada en contexto.
- **n8n**: Orquestador del flujo. Expone un Webhook que recibe las preguntas de los usuarios y las reenvía a la API de Python, devolviendo la respuesta procesada.
- **Modelos**: Utiliza `all-MiniLM-L6-v2` (HuggingFace local) para embeddings y `llama3-8b-8192` (via Groq) como modelo generativo.

## Requisitos Previos

- Python 3.9+
- Una cuenta de n8n (puede ser local o cloud).
- API Key de Groq.

## Levantamiento y Ejecución (Local)

### 1. Configurar Entorno Virtual de Python

Abre una terminal en la raíz del proyecto y ejecuta:

```bash
# Crear entorno virtual
python -m venv venv

# Activar el entorno virtual (Windows)
venv\Scripts\activate
# (Mac/Linux)
# source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Renombra el archivo `.env.example` a `.env` y coloca tu clave de API de Groq:

```env
GROQ_API_KEY=gsk_tu_api_key_aqui
```

### 3. Ingestar Documentos e Iniciar API

Primero, necesitamos leer los documentos que se encuentran en la carpeta `docs/` y generar la base de datos vectorial local.

Levanta el servidor FastAPI:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Abre otra terminal o un cliente como Postman, y ejecuta la ingesta:

```bash
curl -X POST http://localhost:8000/ingest
```
*(Deberías recibir un mensaje indicando cuántos fragmentos fueron indexados y se creará una carpeta `faiss_index`)*.

### 4. Importar el Workflow en n8n

1. Abre n8n.
2. Ve a "Workflows" y haz clic en "Add workflow".
3. Arriba a la derecha, haz clic en el menú (tres puntos) y selecciona **Import from File**.
4. Selecciona el archivo `n8n-workflow.json` proporcionado en este repositorio.
5. Guarda y activa el workflow.
6. Copia la **Test URL** del nodo Webhook (ej. `http://localhost:5678/webhook-test/ask`).

### 5. Probar el Sistema Completo

Envía una pregunta al webhook de n8n:

```bash
curl -X POST http://localhost:5678/webhook-test/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "¿Cómo reinicio el servicio de autenticación?"}'
```

El asistente debería responder basándose estrictamente en la información de los archivos en la carpeta `docs/`.

## Manejo de Errores

- **Preguntas sin respuesta**: Si el sistema no encuentra la respuesta en el contexto, indicará explícitamente que no posee esa información (evitando alucinaciones).
- **Caídas de API**: El código de Python gestiona excepciones y devuelve un error 500 legible. n8n tiene un enrutamiento de errores (`onError`) en el request HTTP que intercepta caídas y devuelve un JSON de error amigable al usuario.
- **Inputs Vacíos**: Si la API recibe una consulta vacía, devuelve un HTTP 400 Bad Request.
