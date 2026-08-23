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

# ── Güvenlik Middleware (Security Headers) ──
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Her HTTP yanıtına kurumsal güvenlik başlıklarını ekler."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# CORS güvenliği — Yalnızca yerel ve güvenilir portlara izin verilir
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
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


MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB sınır (DoS ve bellek tüketim koruması)

@app.post("/api/documents/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Dosyaları 'documents/' dizinine güvenli şekilde kaydeder ve indeksler."""
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    saved_files = []
    skipped_files = []

    for file in files:
        # 1. Dosya adı sanitizasyonu (Path traversal ve tehlikeli karakter koruması)
        raw_name = os.path.basename(file.filename or "document.txt")
        safe_filename = re.sub(r'[^a-zA-Z0-9_\-\.ğüşıöçĞÜŞİÖÇ]', '_', raw_name)
        
        ext = os.path.splitext(safe_filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            skipped_files.append(safe_filename)
            continue

        # 2. Dosya boyutu kontrolü (DoS koruması)
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            skipped_files.append(f"{safe_filename} (50MB boyuttan büyük)")
            continue

        save_path = os.path.join(DOCUMENTS_DIR, safe_filename)
        with open(save_path, "wb") as f:
            f.write(content)
        saved_files.append(safe_filename)

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
async def chat_stream(req: ChatRequest):
    """Server-Sent Events (SSE) protokolü ile asenkron, kesintisiz ve canlı yanıt akışı sunar."""
    # Giriş temizliği: null byte ve aşırı uzun metin sınırlandırması
    question = req.question.replace("\x00", "").strip()[:4000]

    if not question:
        async def invalid_gen():
            payload = json.dumps({
                "type": "error",
                "content": "Lütfen geçerli bir soru yazın."
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        return StreamingResponse(invalid_gen(), media_type="text/event-stream")

    session_id = req.session_id or db.create_session(question[:35])

    if db.get_chunk_count() == 0:
        async def empty_gen():
            payload = json.dumps({
                "type": "error",
                "content": "Veritabanında indeksli doküman bulunmuyor. Lütfen önce dokümanlarınızı indeksleyin."
            }, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        return StreamingResponse(empty_gen(), media_type="text/event-stream")

    # Kullanıcı mesajını kaydet
    db.save_message(session_id=session_id, role="user", content=question)

    async def sse_event_generator():
        t_start = time.time()
        try:
            # 1. Asenkron Hibrit Arama
            sources, context, search_time = await asyncio.to_thread(engine.query_search, question)

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

            # 2. Sistem komutu
            from src.config import SYSTEM_PROMPT, SYSTEM_PROMPT_EN
            import re
            is_english = any(w in re.findall(r'\b\w+\b', question.lower()) for w in ["what", "how", "why", "explain", "where", "the"])
            sys_prompt = SYSTEM_PROMPT_EN.format(context=context) if is_english else SYSTEM_PROMPT.format(context=context)

            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question}
            ]

            # 3. Model çıkarımını asenkron worker thread'de çalıştır (Sıfır kilitlenme)
            full_text = await asyncio.to_thread(model_manager.chat_complete, messages)
            full_text = engine._clean_thinking_tags(full_text)

            # 4. Kelime kelime akıcı yayın
            words = full_text.split(" ")
            for i, w in enumerate(words):
                chunk = w + (" " if i < len(words) - 1 else "")
                chunk_payload = json.dumps({
                    "type": "chunk",
                    "text": chunk
                }, ensure_ascii=False)
                yield f"data: {chunk_payload}\n\n"
                await asyncio.sleep(0.01)

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

        except Exception as exc:
            err_payload = json.dumps({
                "type": "error",
                "content": f"Çıkarım sırasında hata oluştu: {str(exc)}"
            }, ensure_ascii=False)
            yield f"data: {err_payload}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff"
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
