"""
Zenith AI — Kurumsal FastAPI Sunucusu (src/api/server.py)
==========================================================
Microsoft Foundry Local SDK ile çalışan, asenkron SSE canlı akış (streaming)
ve oturum yönetimi sunan yüksek performanslı REST API.
"""

import os
import sys
import time
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Proje kök dizinini sys.path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.config import DOCUMENTS_DIR, SUPPORTED_EXTENSIONS, CHAT_MODEL, EMBEDDING_MODEL
from src.core.models import ModelManager
from src.core.database import VectorDatabase
from src.core.engine import RAGEngine

app = FastAPI(
    title="Zenith AI — Enterprise Local RAG API",
    description="Microsoft Foundry Local SDK tabanlı çevrimdışı RAG motoru",
    version="1.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model ve veritabanı örnekleri
model_manager = ModelManager()
db = VectorDatabase()
engine = RAGEngine(model_manager, db)


@app.on_event("startup")
def startup_event():
    """Sunucu başlarken yerel yapay zeka modellerini hazırlar."""
    try:
        model_manager.initialize()
        model_manager.load_embedding_model()
        model_manager.load_chat_model()
    except Exception as e:
        print(f"⚠️ Model hazırlığı uyarısı: {e}")


@app.on_event("shutdown")
def shutdown_event():
    """Sunucu kapanırken modelleri bellekten boşaltır."""
    try:
        model_manager.shutdown()
    except Exception:
        pass


# ── Pydantic İstek Modelleri ──
class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "Yeni Doküman Analizi"


# ── REST API Uç Noktaları ──

@app.get("/api/health")
def get_health():
    """Sistem ve model sağlık durumu."""
    return {
        "status": "online",
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "offline": True
    }


@app.get("/api/stats")
def get_stats():
    """Veritabanı ve doküman istatistikleri."""
    return db.get_stats()


@app.post("/api/documents/ingest")
def ingest_documents():
    """'documents/' dizinindeki belgeleri vektörleştirir ve FTS5 indeksine kaydeder."""
    result = engine.ingest_documents()
    return result


@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Dosyaları 'documents/' dizinine kaydeder ve indeksler."""
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    saved_files = []
    skipped_files = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            skipped_files.append(file.filename)
            continue

        save_path = os.path.join(DOCUMENTS_DIR, file.filename)
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
        saved_files.append(file.filename)

    ingest_res = engine.ingest_documents()
    return {
        "saved_files": saved_files,
        "skipped_files": skipped_files,
        "total_chunks": ingest_res.get("total_chunks", 0)
    }


@app.delete("/api/database")
def clear_database():
    """Tüm veritabanı indeksini sıfırlar."""
    deleted = db.clear_all()
    return {"deleted_chunks": deleted}


# ── Oturum Yönetimi ──

@app.get("/api/sessions")
def get_sessions():
    """Tüm kayıtlı sohbet oturumlarını döndürür."""
    sessions = db.get_sessions()
    return [{"session_id": s.session_id, "title": s.title, "created_at": s.created_at, "updated_at": s.updated_at} for s in sessions]


@app.post("/api/sessions")
def create_session(req: SessionCreateRequest):
    """Yeni bir sohbet oturumu oluşturur."""
    session_id = db.create_session(req.title or "Yeni Doküman Analizi")
    return {"session_id": session_id, "title": req.title}


@app.get("/api/sessions/{session_id}")
def get_session_messages(session_id: str):
    """Oturuma ait mesajları döndürür."""
    messages = db.get_session_messages(session_id)
    result = []
    for m in messages:
        sources_list = json.loads(m.sources_json) if m.sources_json else []
        result.append({
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "sources": sources_list,
            "search_time": m.search_time,
            "gen_time": m.gen_time,
            "created_at": m.created_at
        })
    return {"session_id": session_id, "messages": result}


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Sohbet oturumunu siler."""
    db.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


# ── SSE Canlı Akış (Streaming Chat) ──

@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """Server-Sent Events (SSE) protokolü ile kelime kelime canlı yanıt akışı sunar."""
    question = req.question.strip()
    session_id = req.session_id or db.create_session(question[:35])

    if db.get_chunk_count() == 0:
        def empty_gen():
            payload = json.dumps({
                "type": "error",
                "content": "Veritabanında indeksli doküman bulunmuyor. Lütfen önce dokümanlarınızı indeksleyin."
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        return StreamingResponse(empty_gen(), media_type="text/event-stream")

    # Kullanıcı mesajını kaydet
    db.save_message(session_id=session_id, role="user", content=question)

    def sse_event_generator():
        t_start = time.time()
        # 1. Hibrit Arama
        sources, context, search_time = engine.query_search(question)

        sources_data = [
            {
                "source_file": s.source_file,
                "chunk_index": s.chunk_index,
                "similarity": s.similarity,
                "relevance": s.relevance_percentage,
                "citation_index": s.citation_index,
                "match_type": s.match_type,
                "content": s.content
            }
            for s in sources
        ]

        # Başlangıç metaveri olayı
        init_payload = json.dumps({
            "type": "meta",
            "search_time": search_time,
            "sources": sources_data,
            "session_id": session_id
        }, ensure_ascii=False)
        yield f"data: {init_payload}\n\n"

        # 2. Geçmiş bağlamını al
        past_msgs = db.get_session_messages(session_id)
        chat_history = [{"role": m.role, "content": m.content} for m in past_msgs]

        # 3. Model çıkarım akışı
        stream_gen = engine.query_generate(question, sources, context, chat_history=chat_history)
        full_text = ""

        for chunk in stream_gen:
            full_text += chunk
            chunk_payload = json.dumps({
                "type": "chunk",
                "text": chunk
            }, ensure_ascii=False)
            yield f"data: {chunk_payload}\n\n"

        gen_time = round(time.time() - t_start, 2)

        # Asistan yanıtını kaydet
        db.save_message(
            session_id=session_id,
            role="assistant",
            content=full_text,
            sources=sources_data,
            search_time=search_time,
            gen_time=gen_time
        )

        # Bitiş olayı
        done_payload = json.dumps({
            "type": "done",
            "full_text": full_text,
            "gen_time": gen_time,
            "search_time": search_time
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ── Derlenmiş React Frontend Statik Dosya Sunumu ──
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """FastAPI sunucusunu Uvicorn ile başlatır."""
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
