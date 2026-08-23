# ⚡ Zenith AI — Enterprise SOTA Local & Private RAG Assistant

**State-of-the-Art Offline Document Intelligence, Hybrid Search (Dense + FTS5 BM25 + RRF), In-Text Citations, Dual-Way Voice AI & Modern React + FastAPI Architecture.**

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Frontend: React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20Tailwind-cyan.svg)](https://react.dev/)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI%20SSE%20Stream-emerald.svg)](https://fastapi.tiangolo.com/)
[![Platform: Local AI](https://img.shields.io/badge/Platform-Microsoft%20Foundry%20Local-indigo.svg)](https://azure.microsoft.com/)
[![Privacy: Zero Leakage](https://img.shields.io/badge/Privacy-100%25%20Offline%20Zero%20Data%20Leakage-emerald.svg)](#-zero-data-leakage--security-architecture)

[🇹🇷 Türkçe Dokümantasyon için tıklayınız](README.tr.md)

---

## 📌 Overview

**Zenith AI** is an institutional-grade, 100% offline Retrieval-Augmented Generation (RAG) assistant powered by **Microsoft Foundry Local**.

Powered by the **Microsoft Foundry Local SDK**, Zenith AI runs local Large Language Models (**`phi-3.5-mini`** 3.8B Instruct) and Dense Embedding Models (**`qwen3-embedding-0.6b`** 1024-dimensional) on your local CPU. With zero cloud dependency, zero external API costs, and zero network calls, all confidential enterprise documents, embeddings, and chat histories remain strictly inside your device.

---

## 🏛️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               FRONTEND: React 18 + Vite + TypeScript + Tailwind CSS                    │
│    (ChatGPT/Perplexity-grade Dark UI, Real-time SSE Token Stream, STT Mic, TTS, Citations) │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / Server-Sent Events (SSE)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND: FastAPI + Uvicorn                                     │
│            (Asynchronous REST API, Multi-Session Management, Zero IPC Deadlock)         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        RAG ENGINE: Hybrid Search & SQLite FTS5                         │
│            (Dense Vectors + SQLite FTS5 BM25 + Reciprocal Rank Fusion RRF)             │
└───────────────────────┬────────────────────────────────────────┬───────────────────────┘
                        │ (Vector & Text Retrieval)              │ (On-Device Inference)
                        ▼                                        ▼
    ┌───────────────────────────────────────┐   ┌────────────────────────────────────────┐
    │    SQLite Local Store & FTS5 Index    │   │      Microsoft Foundry Local SDK       │
    │  - documents (1024-d L2 Vectors)      │   │  - qwen3-embedding-0.6b (1024-d)       │
    │  - documents_fts (unicode61 BM25)     │   │  - phi-4-mini (3.8B Instruct)          │
    │  - chat_sessions & chat_messages      │   └────────────────────────────────────────┘
    └───────────────────────────────────────┘
```

---

## 🌟 Key Features & Engineering Highlights

### 1. 🔍 Hybrid Search Engine (Dense + BM25 + RRF)
- **Dense Vector Search:** 1024-dimensional semantic similarity via `qwen3-embedding-0.6b`.
- **Lexical BM25 Search:** SQLite `FTS5` virtual table with `unicode61` tokenizer for exact keyword, acronym, product name, and error code matching.
- **Reciprocal Rank Fusion (RRF):** Combines both rank spaces into a single calibrated relevance score:
  $$RRF(d) = \frac{\alpha}{k + rank_{dense}(d)} + \frac{1 - \alpha}{k + rank_{bm25}(d)}$$

### 2. 🎯 Grounded In-Text Citations `[1]`, `[2]`
- Perplexity-style inline citation badges embedded directly within the generated answer.
- Hovering over a badge displays an interactive tooltip with source filename, section, calibrated relevance percentage, and verified text snippet.

### 3. 📊 Structure-Aware Document Parsing & Table Preservation
- **Microsoft Excel (`.xlsx`):** Converts tabular rows into Markdown Pipe Tables (`| Col | Val |`) with header retention, ensuring financial and operational numbers remain intact.
- **Microsoft Word (`.docx`) & PDF:** Section heading hierarchy (`#`, `##`, `###`) and slide markers are preserved per chunk.
- **Formats Supported:** `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.txt`.

### 4. 🎙️ Dual-Way Voice AI (Web Speech STT & TTS)
- **Speech-to-Text (STT):** Real-time Turkish voice input via browser-native Web Speech Recognition.
- **Text-to-Speech (TTS):** One-click natural voice playback with WCAG 2.1 accessibility compliance.

### 5. 📁 Multi-Session Chat & Persistent Memory
- Create and switch between multiple document analysis sessions.
- Full SQLite persistence (`chat_sessions` and `chat_messages` tables).
- One-click Markdown report export.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ (for building React frontend)
- Microsoft Foundry Local SDK installed

### 1. Clone & Install Dependencies
```powershell
git clone https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant.git
cd microsoft-foundry-local-rag-assistant

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Build frontend bundle if modified
cd frontend
npm install
npm run build
cd ..
```

### 2. Launch Application
```powershell
python app.py
```

* **Option `[1]`:** Terminal (CLI) Mode (Interactive ANSI console).
* **Option `[2]`:** Web Application (Starts FastAPI server and automatically opens `http://localhost:8000`).

---

## ⚙️ Technical Specifications

| Component | Specification | Details |
|---|---|---|
| **Chat Model** | `phi-4-mini` (3.8B Instruct) | Microsoft Foundry Local on-device CPU inference (~15-20s latency) |
| **Embedding Model** | `qwen3-embedding-0.6b` | 1024-dimensional dense vectors (~600 MB RAM) |
| **Database** | SQLite + FTS5 | Serverless, zero configuration, single file (`data/rag_knowledge.db`) |
| **Search Engine** | Hybrid (Dense + BM25) | Reciprocal Rank Fusion ($k=60, \alpha=0.5$) |
| **Frontend** | React 18 + Vite + Tailwind | Dark Silicon Valley UI, Lucide Icons, SSE live streaming |
| **Backend** | FastAPI + Uvicorn | Asynchronous REST + Server-Sent Events |
| **Cost** | **$0 / 0 TL** | 100% Free, Open Source, Zero Cloud Dependency |

---

## 📜 License & Copyright

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

**Author:** Çağrı Giray Keşan  
**Copyright:** © 2026 Çağrı Giray Keşan. All Rights Reserved.

