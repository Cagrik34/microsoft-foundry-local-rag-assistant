# ⚡ Zenith AI — Enterprise Local & Private RAG Assistant

**High-Performance Offline Document Intelligence, Zero Data Leakage Retrieval-Augmented Generation & Web Speech Voice Engine.**

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform: Local AI](https://img.shields.io/badge/Platform-Microsoft%20Foundry%20Local-indigo.svg)](https://azure.microsoft.com/)
[![Privacy: Zero Leakage](https://img.shields.io/badge/Privacy-100%25%20Offline%20Zero%20Data%20Leakage-emerald.svg)](#-security--zero-data-leakage-architecture)
[![Accessibility: WCAG 2.1](https://img.shields.io/badge/Accessibility-Web%20Speech%20TTS-pink.svg)](#-core-modules--capabilities)

[🇹🇷 Türkçe Dokümantasyon için tıklayınız](https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant/blob/main/README.tr.md)

---

## 📌 Overview

**Zenith AI** is an open-source, institutional-grade local Retrieval-Augmented Generation (RAG) assistant engineered for enterprise document intelligence, confidential corporate analytics, and zero-compromise privacy.

Powered by the **Microsoft Foundry Local SDK**, Zenith AI runs state-of-the-art local Large Language Models (**`phi-3.5-mini`** 3.8B Instruct) and Dense Embedding Models (**`qwen3-embedding-0.6b`** 1024-dimensional) directly on your local CPU/hardware. Operating under a **Zero Data Leakage Architecture**, zero documents, embeddings, telemetry, or query strings ever leave your local machine.

---

## 🏛️ Architecture & Data Flow Diagram

```text
                               ┌────────────────────────────────────────┐
                               │      User Interaction Layer (UI)       │
                               │  [Web (Streamlit)]  |  [Terminal CLI]  │
                               └───────────────────┬────────────────────┘
                                                   │ (Event Dispatch)
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │        RAG Orchestration Engine        │
                               │          (src/core/engine.py)          │
                               └─────────┬────────────────────┬─────────┘
                                         │                    │
                    (Vector Search)      │                    │ (Text Generation)
                                         ▼                    ▼
             ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
             │  SQLite Vector Store (database.py)│    │ Model Manager (src/core/models.py)│
             │   - Pre-Normalized Cosine Engine  │    │   - Persistent ThreadPool Worker  │
             │   - Ghost Chunk Deletion Safeguard│    │   - Stateless ChatClient Factory  │
             └───────────────────────────────────┘    └─────────────────┬─────────────────┘
                                                                        │ (Native C++ gRPC)
                                                                        ▼
                                                      ┌───────────────────────────────────┐
                                                      │    Microsoft Foundry Local SDK    │
                                                      │  - qwen3-embedding-0.6b (1024-d)  │
                                                      │  - phi-3.5-mini (3.8B Instruct)   │
                                                      └───────────────────────────────────┘
```

---

## 🌟 Core Modules & Capabilities

### 1. 🌐 Dual-Mode Interface Architecture
- **Gemini Live Glassmorphic Web Panel (`src/ui/web.py`):** Dynamic gradient mesh animations, floating aura orbs, glassmorphic transparent navigation, drag-and-drop file uploader with deduplication, and exportable Markdown audit trails.
- **Ultra-Lightweight Terminal CLI (`app.py` / `src/ui/cli.py`):** ANSI-styled terminal console with Windows UTF-8 stream decoding (`cp1254` crash-resilient) for headless execution and rapid developer interaction.

### 2. 📑 Multi-Format Ingestion Pipeline (`src/core/document_loader.py`)
- Deep text and structural extraction supporting:
  - **Markdown (`.md`) & Plain Text (`.txt`):** Multi-encoding detection (`utf-8`, `utf-8-sig`, `cp1254`, `latin-1`).
  - **Adobe PDF (`.pdf`):** Multi-page PDF extraction via `pypdf`.
  - **Microsoft Word (`.docx`):** Paragraph and table extraction via `python-docx`.
  - **Microsoft Excel (`.xlsx`):** Multi-sheet tabular parsing via `openpyxl`.
  - **Microsoft PowerPoint (`.pptx`):** Slide and shape text extraction via `python-pptx`.
- **Extraction Error Safeguard:** Parser exceptions and missing libraries gracefully yield empty buffers rather than vectorizing error strings into the knowledge database.

### 3. 🗄️ SQLite Vector Store & Pre-Normalized Cosine Engine (`src/core/database.py`)
- Self-contained serverless SQLite vector store (`data/rag_knowledge.db`).
- **L2 Pre-Normalization:** Embeddings are normalized upon insertion, reducing cosine search complexity to a single matrix dot product (`matrix @ q_vec`).
- **Ghost Chunk Prevention:** Purges stale chunks on document re-indexing before writing new partitions.

### 4. ⚡ RAG Orchestration & Single-Pass Summarization (`src/core/engine.py`)
- **Single-Pass Multi-Document Summarization (`_summarize_per_file`):** Consolidates document previews into a single LLM inference call, eliminating the $O(N)$ serial latency bottleneck (reducing multi-file summary latency from 75s+ down to ~8s).
- **Intelligent Query Intent Routing (`_is_summary_query`):** Distinguishes general document-wide overview requests from specific inquiries ("summarize security vulnerabilities"), preserving semantic vector search for domain-specific queries.
- **Multilingual Support:** Regex-based English language detection dynamically selects the target system prompt.

### 5. 🧠 ThreadPool-Isolated Foundry Local Engine (`src/core/models.py`)
- **Event Loop Deadlock Defense:** C++ native gRPC calls are isolated inside a dedicated `ThreadPoolExecutor(max_workers=1)` to prevent thread starvation against Streamlit's `asyncio` event loop.
- **Stateless Chat Client:** Instantiates fresh `ChatClient` sessions per turn, preventing context window accumulation and CPU memory leakage.

### 6. 🔊 Web Speech Accessibility & Voice AI (`Web Speech API`)
- Zero-cloud, 100% offline text-to-speech synthesis using the browser's native Turkish speech engine.
- One-click screen-reader voice assistant built with WCAG 2.1 accessibility standards in mind.

### 7. 🚪 Instant OS Process Terminus
- Graceful shutdown workflow that frees loaded models from RAM and invokes clean OS process exit (`os._exit(0)` within 0.3s) to eliminate hanging background event loops.

---

## ⚙️ Technical Parameters & Optimized Hyperparameters

| Parameter | Configuration | Engineering Rationale |
|---|---|---|
| **Embedding Model** | `qwen3-embedding-0.6b` | 1024-dimensional multilingual embeddings (~600 MB RAM, sub-second CPU latency) |
| **Chat Model** | `phi-3.5-mini` (3.8B) | Microsoft 3.8B Instruct model; fast CPU decode speed (8-10 tok/s), zero timeout risk |
| **Alternative Chat Model** | `qwen3-4b` | Documented in `src/config.py` for enhanced reasoning and Turkish fluency |
| **Chunk Partition Size** | `1000` characters | Preserves semantic integrity across paragraphs and tabular rows |
| **Chunk Overlap** | `200` characters | Sliding window buffer preventing context boundary truncation |
| **Similarity Threshold** | `0.05` | Cosine similarity baseline filtering noise |
| **Top-K Passages** | `3` passages | Optimal balance between multi-source coverage and CPU prefill speed |
| **Max Context Size** | `1000` characters | Optimized for CPU prefill speed (~280 tokens, 3-4s first token latency) |
| **Max Output Tokens** | `150` tokens | Concise 2-3 sentence structured responses, preventing model verbosity |

---

## 🛠️ Engineering Breakthroughs & Latency Optimizations

### 1. Streamlit AsyncIO & Native C++ gRPC Deadlock Resolution
* **Issue:** Microsoft Foundry SDK's native gRPC driver collided with Streamlit's `asyncio` loop on the main thread, resulting in 180s freezes and `Operation was cancelled` timeouts.
* **Resolution:** All embedding generation and chat completions are routed through a persistent `ThreadPoolExecutor(max_workers=1)` isolated worker.

### 2. Multi-File Summarization Latency Reduction ($O(N) \to O(1)$)
* **Issue:** Summarizing $N$ indexed files previously fired $N$ sequential synchronous LLM calls ($N \times 25\text{s} = 75\text{s}+$).
* **Resolution:** Re-engineered into a consolidated contextual prompt, generating complete multi-file executive summaries in a single ~8s inference call.

### 3. Ghost Chunks & L2 Pre-Normalization
* **Issue:** Re-indexing shortened files left stale orphan chunks in SQLite (`INSERT OR REPLACE` only updated matching indices).
* **Resolution:** Implemented pre-deletion (`DELETE FROM documents WHERE source_file = ?`) and unit L2 vector storage.

### 4. Windows UTF-8 Terminal Crash Defense
* **Issue:** Windows command prompt codepages (`cp1254`/`cp1252`) raised `UnicodeEncodeError` when printing status emojis.
* **Resolution:** Integrated runtime UTF-8 stream wrappers on `sys.stdout` and `sys.stderr` in both `app.py` and `src/ui/cli.py`.

---

## 🚀 Getting Started

### Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Python 3.11 or higher
- **RAM:** Minimum 8 GB (16 GB recommended)
- **Disk:** ~3 GB free space (models downloaded once on first launch)

### 1. Clone & Install Dependencies

```bash
# Clone the repository
git clone https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant.git
cd microsoft-foundry-local-rag-assistant

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch Application

```bash
python app.py
```

The interactive launch screen allows you to select your preferred execution mode:

```text
╭─────────────────────────────────────────────────────────────╮
│  ⚡ ZENITH AI — Yerel RAG Akıllı Asistanı                   │
│  🔒 Tamamen Çevrimdışı • Gizli • Güvenli Yerel AI           │
├─────────────────────────────────────────────────────────────┤
│  🚀 Çalıştırma Modunu Seçin:                                │
│                                                             │
│   [1] 💻 Terminal (CLI) Modu                                │
│   [2] 🌐 Web Arayüzü (Streamlit — Tarayıcıda Açılır)        │
╰─────────────────────────────────────────────────────────────╯
```

* **Option `1` (or Enter):** Starts the fast command-line terminal interface.
* **Option `2`:** Launches the modern Gemini Live-style Streamlit web portal in your default browser.
* *(Direct Web UI launch: `streamlit run src/ui/web.py`)*

---

## 📁 Directory Structure

```text
microsoft-foundry-local-rag-assistant/
├── documents/                  # Ingestion directory (.md, .txt, .pdf, .docx, .xlsx, .pptx)
├── data/                       # Local SQLite vector database (rag_knowledge.db)
├── src/                        # Modular source code
│   ├── __init__.py             # Source package root
│   ├── config.py               # Hyperparameters, prompt templates, model selection
│   ├── core/                   # Core AI & RAG Engine
│   │   ├── __init__.py         # Core package definition
│   │   ├── models.py           # Thread-safe Foundry SDK manager & stateless client
│   │   ├── document_loader.py  # Multi-format document parser & text chunking
│   │   ├── database.py         # SQLite vector store & normalized cosine search
│   │   └── engine.py           # RAG query coordinator & single-pass summarizer
│   └── ui/                     # User interfaces
│       ├── __init__.py         # UI package definition
│       ├── cli.py              # UTF-8 resilient CLI with live word streaming
│       └── web.py              # Streamlit web UI (Web Speech TTS, Glassmorphism)
├── app.py                      # Application entrypoint
├── requirements.txt            # Python dependencies
├── README.md                   # Institutional English documentation
├── README.tr.md                # Kapsamlı Türkçe dokümantasyon
├── LICENSE                     # MIT License
└── .gitignore                  # Git ignore rules
```

---

## 🛡️ Security & Zero Data Leakage Architecture

- **100% Offline Execution:** All neural network weights, vector embeddings, and generation pipelines execute locally via Microsoft Foundry Local SDK.
- **Zero Telemetry & Cloud Exfiltration:** No external network requests, API keys, or third-party cloud services are utilized.
- **In-Memory Sanitization:** Streamlit chat sessions and cached contexts are maintained strictly in local session memory.

---

## 📜 License & Copyright

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

**Author:** Çağrı Giray Keşan  
**Copyright:** © 2026 Çağrı Giray Keşan. All Rights Reserved.

