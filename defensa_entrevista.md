# Guía para la Defensa de la Prueba Técnica (Entrevista)

Este documento está diseñado para ayudarte a defender la arquitectura, el código y las decisiones de diseño tomadas durante la implementación de tu prueba técnica en la entrevista.

---

## 1. ¿Qué hiciste paso a paso? (El Elevator Pitch)

Cuando te pidan que expliques tu solución, puedes usar este resumen paso a paso:

1. **Análisis y Diseño de la Arquitectura**: Comprendí que el objetivo era construir un sistema RAG (Retrieval-Augmented Generation). Decidí utilizar **FastAPI en Python** para manejar el motor pesado (procesamiento de datos e IA) porque Python tiene el mejor ecosistema para Machine Learning (LangChain, FAISS). Luego, usé **n8n** como la capa de orquestación y enrutamiento (Gateway) para recibir el webhook HTTP y derivarlo al motor.
2. **Ingesta de Documentos (Python)**: Creé un módulo `ingestion.py` que iterara sobre la carpeta `/docs`. Como había varios formatos (PDF, TXT, MD, JSON), implementé lectores específicos para cada uno usando librerías estándar y `pypdf`. Luego, limpié el texto mediante expresiones regulares (regex) para remover ruido, saltos de línea innecesarios y caracteres raros. Finalmente, utilicé `RecursiveCharacterTextSplitter` de LangChain para dividir los textos largos en "chunks" (fragmentos) de tamaño fijo con un "overlap" (solapamiento) para no perder el contexto semántico en los bordes de cada corte.
3. **Base de Datos Vectorial (Python)**: En `vector_store.py`, tomé esos chunks y generé sus embeddings utilizando el modelo local `all-MiniLM-L6-v2` mediante `HuggingFaceEmbeddings`. Decidí procesar los embeddings localmente para evitar depender de créditos de pago en APIs externas. Guardé estos embeddings en **FAISS** (Facebook AI Similarity Search). Elegí FAISS porque es extremadamente rápido, funciona en memoria y puede persistir el índice en un archivo en el disco sin necesidad de levantar contenedores Docker adicionales, cumpliendo el requisito de "levantarse localmente".
4. **Búsqueda Semántica y Chatbot (Python)**: Construí la lógica donde, dada una pregunta de usuario, el sistema genera el embedding de la pregunta, busca en FAISS los top 3 (k=3) fragmentos más similares y envía esos fragmentos como contexto estricto junto con la pregunta al modelo **Llama 3** (8B) utilizando la API gratuita ultrarrápida de **Groq**. Implementé un **System Prompt** muy restrictivo que obliga al LLM a contestar SOLO basándose en el contexto y a decir que "no sabe" si la respuesta no se encuentra en el texto.
5. **FastAPI y Manejo de Errores (Python)**: Empaqueté todo en una API con FastAPI (`main.py`) con endpoints separados para ingesta (`/ingest`) y consulta (`/query`), añadiendo bloques `try-except` que retornan códigos HTTP 500 y 400 detallados en caso de timeouts o fallos de la API de OpenAI o requests vacíos.
6. **Workflow en n8n**: Construí un workflow de n8n simple pero robusto. Inicia con un **Webhook Node**, realiza un **HTTP Request Node** contra la API de FastAPI que construí, y tiene ramas separadas para respuestas exitosas o errores (Catch/Error Node), retornando el payload final al usuario de manera limpia.

---

## 2. Posibles Preguntas de la Entrevista y Respuestas Sugeridas

### Pregunta 1: ¿Por qué elegiste hacer el procesamiento en Python y por qué Groq en lugar de OpenAI?
**Respuesta:** *"Si bien n8n tiene nodos nativos de IA, el enunciado pedía que Python se encargara del procesamiento, chunking, limpieza, embeddings y búsqueda semántica. Por otro lado, decidí usar **Groq** en lugar de OpenAI porque Groq proporciona acceso al modelo abierto Llama 3 a velocidades increíblemente rápidas (LPUs) con una capa 100% gratuita, ideal para evitar problemas de cuota (Rate Limits o Insufficient Quota). Para los embeddings, elegí procesarlos localmente en mi CPU con `HuggingFaceEmbeddings` (MiniLM) para demostrar que puedo construir un motor de búsqueda semántica autosuficiente."*

### Pregunta 2: Explicame tu estrategia de Chunking. ¿Por qué usaste `RecursiveCharacterTextSplitter` y qué son esos valores (1000 y 200)?
**Respuesta:** *"Usé `RecursiveCharacterTextSplitter` porque es la mejor práctica general. No divide los textos a la fuerza, sino que intenta dividirlos primero por párrafos (doble salto de línea), luego por frases (punto) y finalmente por espacios. Esto preserva la estructura lógica del lenguaje natural. Definí un `chunk_size` de 1000 caracteres como un tamaño intermedio que le da suficiente contexto al LLM sin inundar la ventana de tokens, y un `chunk_overlap` de 200 caracteres. El solapamiento es crucial para que, si un concepto clave justo se corta a la mitad, la cola del chunk anterior y la cabeza del chunk siguiente contengan la frase completa, asegurando que el buscador semántico no la pase por alto."*

### Pregunta 3: ¿Por qué utilizaste FAISS y no una base de datos más robusta como Pinecone, ChromaDB o Qdrant?
**Respuesta:** *"El requerimiento era que la solución debe poder levantarse de manera local y sencilla. Pinecone es cloud, lo que rompe ese requisito si no hay conexión a base de datos externa. ChromaDB o Qdrant son excelentes, pero FAISS (desarrollado por Meta) es una librería puramente en memoria, ultraligera, que no levanta puertos ni procesos de servidor extra y permite serializar el índice en un archivo en disco muy fácilmente. Para este volumen documental estático y enfocado a una prueba técnica, FAISS provee la máxima eficiencia y cero fricción de instalación."*

### Pregunta 4: ¿Cómo garantizas que la IA no alucine (no invente información) y cumpla con el requerimiento de "Si la info no existe, indicarlo explícitamente"?
**Respuesta:** *"Lo garantizo mediante tres mecanismos fundamentales del framework RAG (Retrieval-Augmented Generation):
1. **Temperatura 0**: Configuramos el modelo de OpenAI en la API con `temperature=0.0`. Esto hace que el modelo sea determinista y se concentre en los hechos, reduciendo su "creatividad".
2. **Inyección estricta de Contexto**: La pregunta del usuario no se envía sola. Se ensambla en un bloque donde la estructura principal es el documento recuperado por FAISS.
3. **Prompt de Sistema Restrictivo**: Utilicé un `system_prompt` directo: 'Tu tarea es responder... basándote ÚNICAMENTE en la documentación proporcionada... Si la respuesta NO se encuentra, DEBES responder explícitamente: Lo siento, no tengo información...'. Esto corta la libertad del LLM de divagar."*

### Pregunta 5: ¿Cómo manejas los errores de la API, timeouts o preguntas vacías?
**Respuesta:** *"En FastAPI implementé bloques `try-except`. Si el parámetro `question` llega vacío en el Payload JSON, lanzo una `HTTPException` con status `400 Bad Request`. Si falla FAISS (porque el índice no está creado), o si la librería de OpenAI sufre un Timeout/Rate Limit, esto levanta una excepción nativa de Python que intercepto y devuelvo al cliente como un `HTTP 500 Internal Server Error` acompañado del detalle técnico. A su vez, el flujo en n8n está diseñado para capturar estos fallos en su HTTP Request Node para no caerse y devolver siempre un Webhook Response estructurado indicando que el servicio no está disponible."*

### Pregunta 6: ¿Qué pasa si te damos un PDF desordenado o con tablas cruzadas? (Manejo de documentos)
**Respuesta:** *"Para PDF estoy usando `pypdf`, que extrae texto plano pero muchas veces no comprende las estructuras complejas como columnas. Implementé un método de limpieza `clean_text` que normaliza espacios y saltos de línea para unificar la lectura. Si estuviéramos en un escenario productivo más complejo con tablas importantes o imágenes en los PDF, sugeriría cambiar a un parseador más avanzado (como Unstructured.io) o aplicar OCR (como Tesseract), pero para el contexto de la prueba la extracción textual sumada a la normalización regex es la opción más limpia y eficiente."*

---

¡Éxitos en la entrevista! Recuerda mostrar seguridad en las decisiones tomadas. Lo importante no es tener la respuesta perfecta, sino poder argumentar el "por qué" de cada elección técnica que tomaste.
