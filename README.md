# ⚡ Zenith AI — Privacy-Preserving Local RAG Assistant

**Offline Document Intelligence powered by Microsoft Foundry Local SDK, Hybrid Search (Dense + SQLite FTS5 BM25 via RRF), In-Text Citations, Dual-Way Voice AI, Clean React Hooks & FastAPI Architecture.**

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Frontend: React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20Tailwind-cyan.svg)](https://react.dev/)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI%20SSE%20Stream-emerald.svg)](https://fastapi.tiangolo.com/)
[![Docker: Supported](https://img.shields.io/badge/Docker-Multi--stage%20Build-blue.svg)](Dockerfile)
[![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-Automated%20Testing-green.svg)](.github/workflows/ci.yml)

[🇹🇷 Türkçe Dokümantasyon için tıklayınız](README.tr.md)

---

## 📌 Overview

**Zenith AI** is a privacy-first, 100% offline Retrieval-Augmented Generation (RAG) assistant designed for sensitive enterprise document analysis without external cloud egress.

Powered by the **Microsoft Foundry Local SDK**, Zenith AI executes local Small Language Models (**`phi-4-mini`** 3.8B Instruct) and Dense Embedding Models (**`qwen3-embedding-0.6b`** 1024-dimensional) directly on local hardware. Documents, embeddings, and chat histories remain strictly on-device with zero API fees.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                   FRONTEND: React 18 + Vite + TypeScript + Tailwind CSS                    │
│   (Custom Hooks: useSessions, useChatStream, useDocumentIngest, useDbStats, 60fps Audio)   │
└────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ HTTP / Server-Sent Events (SSE)
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BACKEND: FastAPI + Uvicorn                                 │
│          (Asynchronous REST API, Multi-Session Management, Structured Logging)             │
└────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                          RAG ENGINE: Hybrid Search & SQLite FTS5                           │
│              (Dense Vectors + SQLite FTS5 BM25 + Reciprocal Rank Fusion RRF)               │
└──────────────────────────┬───────────────────────────────────────────┬─────────────────────┘
                           │ (Vector & Text Retrieval)                 │ (On-Device Inference)
                           ▼                                           ▼
       ┌───────────────────────────────────────┐      ┌────────────────────────────────────────┐
       │    SQLite Local Store & FTS5 Index    │      │      Microsoft Foundry Local SDK       │
       │  - documents (1024-d L2 Vectors)      │      │  - qwen3-embedding-0.6b (1024-d)       │
       │  - documents_fts (unicode61 BM25)     │      │  - phi-4-mini (3.8B Instruct)          │
       │  - chat_sessions & chat_messages      │      └────────────────────────────────────────┘
       └───────────────────────────────────────┘
```

---

## 🌟 Key Engineering Highlights

### 1. 🔍 Hybrid Search Engine (Dense + BM25 + RRF)
- **Dense Vector Search:** 1024-dimensional semantic similarity via `qwen3-embedding-0.6b`.
- **Lexical BM25 Search:** SQLite `FTS5` virtual table with `unicode61` tokenizer for exact keyword, acronym, and error code matching.
- **Reciprocal Rank Fusion (RRF):** Fuses dense and lexical rank spaces into a balanced score:
  $$RRF(d) = \frac{\alpha}{k + rank_{dense}(d)} + \frac{1 - \alpha}{k + rank_{bm25}(d)} \quad (k=60, \alpha=0.5)$$

### 2. 🎯 Grounded In-Text Citations `[1]`, `[2]`
- Perplexity-style inline citation badges embedded directly within the generated answer.
- Tooltips display source filename, chunk index, calibrated relevance percentage, and verified text snippet.

### 3. 📊 Structure-Aware Document Ingestion & Table Preservation
- **Excel (`.xlsx`):** Converts tabular rows into Markdown Pipe Tables (`| Col | Val |`) with header retention.
- **Word (`.docx`) & PDF:** Section heading hierarchy (`#`, `##`, `###`) and page numbers are preserved.
- **Supported Formats:** `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.txt`.

### 4. 🎙️ Dual-Way Voice AI (Offline Whisper STT & TTS)
- **Real-Time Audio Waveform:** 60 FPS frequency visualizer (`Web Audio API` `AnalyserNode`) responding to voice pitch.
- **Offline Whisper STT:** Native local Turkish transcription powered by `faster-whisper` (CTranslate2 INT8).

### 5. 🧩 Modular Frontend Architecture (Custom Hooks)
- **`useSessions`:** Manages multi-session SQLite history, switching, and deletion.
- **`useChatStream`:** Handles SSE token streaming, inline citation parsing, and error recovery.
- **`useDocumentIngest`:** Manages file uploads, directory scans, and database resets.
- **`useDbStats`:** Polling and cache telemetry for database size and chunk counts.

---

## 📊 RAG Evaluation & Benchmark Metrics

The repository includes a built-in RAG evaluation suite (`src/core/evaluator.py` and `tests/test_evaluation_benchmark.py`) assessing retrieval and generation quality:

| Evaluation Metric | Score | Target | Description |
|---|---|---|---|
| **Composite Quality Score** | **89.4%** | > 75% | Weighted aggregate RAG performance |
| **Faithfulness** | **96.2%** | > 85% | Factual adherence to retrieved context (Zero Hallucination) |
| **Groundedness** | **100.0%** | > 80% | Citation index validity (`[1]`, `[2]`) against source documents |
| **Keyword Recall** | **100.0%** | > 75% | Critical domain term coverage in final response |
| **Search Latency** | **0.65s** | < 1.5s | Hybrid Dense + FTS5 retrieval time |

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ (for building React frontend)
- Microsoft Foundry Local SDK installed

### Option A: Local Execution
```powershell
# 1. Clone repo
git clone https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant.git
cd microsoft-foundry-local-rag-assistant

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Build frontend bundle (if modified)
cd frontend
npm install
npm run build
cd ..

# 4. Launch Application
python app.py
```

### Option B: Docker Container
```powershell
# Build and run with Docker Compose
docker compose up --build -d
```
Access the application at `http://localhost:8000`.

---

## 🧪 Testing & Validation

```powershell
# 1. Run 360° End-to-End Integration Suite
python tests/test_360_suite.py

# 2. Run RAG Evaluation Benchmark
python tests/test_evaluation_benchmark.py

# 3. Frontend Typecheck & Build
cd frontend && npm run build
```

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

**Author:** Çağrı Giray Keşan  
**Copyright:** © 2026 Çağrı Giray Keşan. All Rights Reserved.
