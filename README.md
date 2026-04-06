# ChadGPT

Bun frontend + Python backend for Chad-focused Q&A using a local RAG knowledge base, with optional OpenRouter integration.

## Prerequisites

- Bun
- Python 3.8+

## Install

```bash
bun install
python3 -m pip install -r backend/requirements.txt
```

If your system blocks global `pip` installs (PEP 668), use a virtual environment:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
```

## Run

Start frontend and backend together via Bun:

```bash
bun run dev
```

Or run each side separately:

```bash
bun run dev:client
bun run dev:server
```

## URLs

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Environment

Optional OpenRouter API key:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
```

Without a key, the backend returns answers from the local RAG knowledge base.

## API

- `POST /api/ask` with `{ "question": "..." }`
- `GET /api/knowledge`
