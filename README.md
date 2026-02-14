# Medical Chatbot

A lightweight medical question-answering API that retrieves medical content from PDF documents, builds a Pinecone vector index of document chunks, and answers user questions using a Mistral-powered conversational chain with Redis-backed per-user conversation memory.

This repository is designed to be run locally or in Docker. It ships with an example PDF in `data/Medical_book.pdf` used for building the vector index.

---

## Highlights

- FastAPI server with simple endpoints to start a session and ask questions
- Document ingestion pipeline: PDF loader → text extraction → chunking → Pinecone vector store
- Retrieval-augmented generation (RAG) with Mistral LLM + Mistral embedding model
- Conversation memory persisted in Redis (per-user sessions)
- Docker-ready

---

## Quick links

- API: `POST /session/start`, `POST /chat`
- Main entrypoint: `app.py`
- Pipelines: `src/pipeline/*`
- Prompt template: `src/helper.py` (edit carefully — contains assistant behavior & safety rules)

---

## Prerequisites

- Python 3.11
- Redis (for conversation storage)
- Pinecone account (API key + environment) or compatible vector store configured the same way the repo expects
- Mistral API access (Mistral embeddings and chat)
-  Langsmith key for tracing


---

## Required environment variables

Create a `.env` in the project root (or export env vars) with the following values:

- MISTRAL_API_KEY — API key for Mistral Chat/Embeddings
- REDIS_URL — Redis connection url (example: `redis://localhost:6379/0`)
- LANGSMITH_API_KEY — optional; set for tracing (empty string is accepted)
- PINECONE_API_KEY — Pinecone API key (if using Pinecone)
- PINECONE_ENV / PINECONE_ENVIRONMENT — Pinecone environment/region identifier (typical var names; set according to your Pinecone setup)

Note: The repository uses the Pinecone client library (`pinecone.Pinecone()`). Configure whatever Pinecone-related environment variables your Pinecone Python SDK version requires (common ones are listed above). Keep API keys secret.

Example `.env`:
```
MISTRAL_API_KEY=sk-...
REDIS_URL=redis://localhost:6379/0
LANGSMITH_API_KEY=
PINECONE_API_KEY=pc-...
PINECONE_ENV=us-east1-gcp
```

---

## Install (local)

1. Clone the repo and change into it:
   ```
   git clone https://github.com/Soumya-RanjanBhoi/medical-chatbot.git
   cd medical-chatbot
   ```

2. (Optional) Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows
   ```

3. Install dependencies:
   ```
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Create `.env` and set the required environment variables (see previous section).

5. Start Redis if you need a local Redis instance (see "Prerequisites").

6. Start the app:
   ```
   python app.py
   ```
   or with uvicorn for development:
   ```
   uvicorn app:app --host 0.0.0.0 --port 8080 --reload
   ```

Notes:
- On first run the pipeline will try to initialize Pinecone, check/create the index, and if the index is empty it will process PDFs from `./data` and populate the vector store. This can take time depending on the document size and the embedding model/API speed.

---

## Docker (quickstart)

1. Build the image:
   ```
   docker build -t medical-chatbot:latest .
   ```

2. Run Redis (if you don't have one already):
   ```
   docker run -d --name redis -p 6379:6379 redis:7
   ```

3. Run the container (replace env values):
   ```
   docker run -it --rm \
     -e MISTRAL_API_KEY="sk-..." \
     -e REDIS_URL="redis://host.docker.internal:6379/0" \
     -e PINECONE_API_KEY="pc-..." \
     -e PINECONE_ENV="us-east1-gcp" \
     -p 8080:8080 \
     medical-chatbot:latest
   ```
   - If running Docker on Linux, set `REDIS_URL=redis://host.docker.internal:6379/0` or use container networking and a Docker network to connect containers.

---

## API

Start a session, then send chat messages. The server sets a `user_no` cookie to track sessions.

1. Start a session (creates a user id and cookie)
   ```
   curl -i -X POST http://localhost:8080/session/start -c cookies.txt
   ```
   Example response:
   ```
   HTTP/1.1 200 OK
   Set-Cookie: user_no=1; Path=/; HttpOnly; SameSite=lax
   {"user_no": 1}
   ```

2. Ask a question (use the cookie created by /session/start)
   ```
   curl -X POST http://localhost:8080/chat \
     -b cookies.txt \
     -d "question=What are the symptoms of disease X?"
   ```
   Example response:
   ```
   {"answer": "The assistant's answer ..."}
   ```

Notes:
- If you POST to `/chat` without the cookie, you'll receive a 401 response: `{"message":"Session not started"}`
- The server expects form-encoded data for `question` (e.g., curl `-d` or typical HTML form).

---

## How it works (architecture & key components)

High-level flow:
1. App startup (`app.py`) initializes `MainPipeline` and a `UserManager`.
2. `MainPipeline` inherits from `initializePinecone`:
   - Connects to Pinecone and Mistral embedding model.
   - Calls `create_vectorstore()`:
     - If the Pinecone index exists and has vectors, loads it; otherwise:
       - `ProcessPipeline` loads PDFs from `data/` (DirectoryLoader + PyPDFLoader)
       - Extracts useful metadata & page content
       - Splits text into chunks using `RecursiveCharacterTextSplitter`
       - Stores embeddings + chunks to Pinecone via `PineconeVectorStore.from_documents`
   - Creates a retriever (MMR search) for RAG.
3. Query handling (`MainPipeline.query`):
   - Loads per-user chat history from Redis (`RedisChatMessageHistory`)
   - Uses `ConversationSummaryBufferMemory` (LLM-based summary) as memory
   - Composes a chat prompt (system template in `src/helper.py` + conversation history)
   - Calls Mistral Chat LLM (via `langchain_mistralai.ChatMistralAI`) to generate an answer

Key files:
- `app.py` — FastAPI server, endpoints
- `src/pipeline/vectorstore.py` — Pinecone integration & vectorstore lifecycle
- `src/pipeline/process_pipeline.py` — PDF loading, filtering, chunking
- `src/pipeline/main_pipeline.py` — high-level orchestration, retriever + conversational chain
- `src/helper.py` — assistant system prompt & behavioral rules
- `src/logger.py` — logging setup (creates `logs/` directory and timestamped log files)
- `src/exception.py` — simple CustomException wrapper

---

## Customization

- Edit the assistant behavior and safety rules in `src/helper.py` (this defines the "system prompt").
  - Be careful: this prompt is intentionally strict (no diagnosing, no external knowledge).
- Add or remove PDF documents in `data/` to change the knowledge base; reindexing occurs automatically if the index is empty. If you need to force reindexing, delete the Pinecone index (via Pinecone UI/CLI) and restart the app.
- Tweak vectorstore/retriever settings (k, fetch_k, lambda_mult) in `src/pipeline/vectorstore.py` and `create_retriever()` calls.
- LLM & embedding model options are configured in `main_pipeline.py` & `vectorstore.py` — update model names or parameters there.

---

## Logging & Troubleshooting

- Logs are created by `src/logger.py` under a `logs/<timestamp>/<timestamp>.log` path in the working directory.
- Common issues:
  - "REDIS_URL not set" — ensure `REDIS_URL` is present in `.env` or environment.
  - "MISTRAL_API_KEY not set" — set `MISTRAL_API_KEY`.
  - Pinecone authentication errors — ensure your Pinecone API key and environment variables are set correctly.
  - Long startup times — initial vector index creation (embedding many pages) may take time and API quota; monitor logs for progress.
- If the vector index has no vectors and you don't want automatic ingestion, remove PDFs from `data/` or pre-populate the index.

---

## Development notes

- The repository is intentionally minimal and focuses on the ingestion + retrieval + chat loop.
- To quickly scaffold missing files used during development, there is a small helper `template.sh`.
- The current `requirements.txt` pins many libraries; consider creating a trimmed `requirements-dev.txt` for development.
- Tests are not included.

---

## Security & Privacy

- The assistant prompt (`src/helper.py`) includes strict safety rules: it will avoid diagnoses and speculative answers. Do not rely on this system for medical diagnoses — it is for informational assistance based only on the provided documents.
- Do not commit `.env` or any secrets to the repository.
- Be mindful of usage costs for LLM and embedding APIs.

---

## Contributing

Contributions are welcome. Suggested workflow:
1. Fork the repo
2. Make changes in a feature branch
3. Open a pull request with a clear description of changes

Please include tests and update the README for any behavioral changes.

---

## License

This repository does not currently include a license file. Add an appropriate open-source license file (e.g., MIT) if you plan to distribute.

---

## Example troubleshooting commands

- Check server is running:
  ```
  curl http://localhost:8080/health
  ```
- Inspect logs directory:
  ```
  ls -R logs || echo "No logs created yet"
  tail -n 200 logs/<most_recent_log_file>
  ```

---

If you'd like, I can:
- Add an example Postman collection for the API endpoints
- Add a script to force reindexing or to precompute embeddings locally
- Create a minimal test suite for the API
