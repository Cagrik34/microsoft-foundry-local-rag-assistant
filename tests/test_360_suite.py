"""
Zenith AI — 360-Derece Kapsamlı Üretim Öncesi Test Süiti (tests/test_360_suite.py)
================================================================================
Uygulamanın tüm katmanlarını (Parser, Vektör DB, FTS5 BM25, Hibrit Arama, RAG Motoru,
FastAPI REST + SSE Akışı ve Güvenlik/Edge Durumları) uçtan uca doğrular.
"""

import os
import sys
import time
import json
import tempfile
import unittest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from starlette.testclient import TestClient
from src.config import DOCUMENTS_DIR, CHAT_MODEL, EMBEDDING_MODEL
from src.core.document_loader import read_document, chunk_text, process_document, scan_documents, process_all_documents
from src.core.database import VectorDatabase
from src.core.models import ModelManager
from src.core.engine import RAGEngine
from src.api.server import app


class TestZenithAI360(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*70)
        print("  ⚡ ZENITH AI — 360° ÜRETİM ÖNCESİ TEST SÜİTİ BAŞLATILIYOR")
        print("="*70)
        cls.models = ModelManager()
        cls.models.initialize()
        cls.models.load_embedding_model()
        cls.models.load_chat_model()
        cls.db = VectorDatabase()
        cls.engine = RAGEngine(cls.models, cls.db)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        print("\n" + "="*70)
        print("  🧹 Test tamamlandı, modeller bellekten boşaltılıyor...")
        cls.models.shutdown()
        print("="*70 + "\n")

    # ── 1. DOKÜMAN AYRIŞTIRICI & PARSER EDGE CASE TESTLERİ ──

    def test_01_empty_and_nonexistent_files(self):
        """Olmayan veya boş dosyalarda çökme koruması testi."""
        res_nonexistent = read_document("non_existent_file.pdf")
        self.assertEqual(res_nonexistent.content, "")

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
            f.write("")
            tmp_path = f.name
        try:
            doc = process_document(tmp_path)
            self.assertEqual(len(doc.chunks), 0)
        finally:
            os.remove(tmp_path)

    def test_02_unicode_and_encoding_resilience(self):
        """Farklı Türkçe ve Latin karakter kodlamaları (UTF-8, CP1254, Latin-1) testi."""
        test_text = "Şirket bütçesi 2.340.000 TL ve kâr oranı %28,5 olarak gerçekleşti. ğüşıöç ĞÜŞİÖÇ."
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="wb") as f:
            f.write(test_text.encode("cp1254"))
            tmp_path = f.name
        try:
            doc = read_document(tmp_path)
            self.assertIn("Şirket bütçesi", doc.content)
            self.assertIn("2.340.000 TL", doc.content)
        finally:
            os.remove(tmp_path)

    def test_03_chunking_integrity(self):
        """Öbekleme bütünlüğü ve karakter sınırları testi."""
        sample_text = ("Paragraf 1: Kurumsal mimari ve güvenlik ilkeleri.\n\n" * 40)
        chunks = chunk_text(sample_text)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertGreaterEqual(len(c), 50)

    # ── 2. VEKTÖR VERİTABANI & HİBRİT FTS5 BM25 TESTLERİ ──

    def test_04_database_clear_and_ingestion(self):
        """Veritabanı sıfırlama, toplu indeksleme ve öbek koruma testi."""
        ingest_res = self.engine.ingest_documents()
        self.assertGreater(ingest_res["total_chunks"], 0)
        self.assertGreater(ingest_res["total_files"], 0)

        stats = self.db.get_stats()
        self.assertGreater(stats["total_chunks"], 0)
        self.assertGreater(stats["db_size_mb"], 0)

    def test_05_hybrid_search_accuracy(self):
        """Dense Vektör + FTS5 BM25 Hibrit Arama Doğruluk Testi."""
        q = "Proje bütçesi ve maliyet"
        sources, context, search_time = self.engine.query_search(q, top_k=3)
        self.assertGreater(len(sources), 0)
        self.assertLess(search_time, 5.0)  # Arama 5 saniyeden kısa sürmeli
        # En az bir kaynak bütçe verisini içermeli
        combined = " ".join([s.content for s in sources])
        self.assertTrue("2.340.000" in combined or "Bütçe" in combined or "Butce" in combined)

    # ── 3. MODEL ÇIKARIMI & SORU-CEVAP KALİTESİ ──

    def test_06_rag_inference_speed_and_grounding(self):
        """phi-4-mini ile RAG soru-cevap doğruluğu ve hız testi."""
        q = "Proje toplam bütçesi kaç TL'dir?"
        sources, context, search_time = self.engine.query_search(q, top_k=2)
        self.assertGreater(len(sources), 0)

        t0 = time.time()
        gen = self.engine.query_generate(q, sources, context)
        answer = "".join(list(gen))
        gen_time = time.time() - t0

        print(f"\n   [TEST METRİK] Soru: '{q}'")
        print(f"   [TEST METRİK] Arama Süresi: {search_time:.2f}s | Çıkarım Süresi: {gen_time:.2f}s")
        print(f"   [TEST METRİK] Üretilen Yanıt: {answer.strip()}")

        self.assertIn("2.340.000", answer)
        self.assertLess(gen_time, 45.0)  # CPU'da makul süre testi

    def test_07_unanswerable_query_fallback(self):
        """Belgelerde olmayan soruya sorumlu yapay zeka geri bildirimi testi."""
        q = "Mars gezegenindeki su kaynakları ve madencilik faaliyetleri nelerdir?"
        sources, context, search_time = self.engine.query_search(q, top_k=2)
        gen = self.engine.query_generate(q, sources, context)
        answer = "".join(list(gen))

        print(f"\n   [TEST METRİK] Kapsam Dışı Soru Yanıtı: {answer.strip()}")
        self.assertTrue(
            "yer almamaktadır" in answer.lower() or
            "bulunmuyor" in answer.lower() or
            "not found" in answer.lower() or
            "belgelerde" in answer.lower()
        )

    # ── 4. FASTAPI REST & SSE CANLI AKIŞ TESTLERİ ──

    def test_08_fastapi_rest_endpoints(self):
        """Tüm REST API uç noktalarının (Health, Stats, Sessions) HTTP 200 testi."""
        # Health
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["chat_model"], "phi-4-mini")

        # Stats
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_chunks", res.json())

        # Create session
        res = self.client.post("/api/sessions", json={"title": "Test Oturumu 360"})
        self.assertEqual(res.status_code, 200)
        sess_id = res.json()["session_id"]

        # Get sessions
        res = self.client.get("/api/sessions")
        self.assertEqual(res.status_code, 200)

        # Delete session
        res = self.client.delete(f"/api/sessions/{sess_id}")
        self.assertEqual(res.status_code, 200)

    def test_09_fastapi_sse_streaming(self):
        """Server-Sent Events (SSE) canlı akış protokol testi."""
        res = self.client.post("/api/chat/stream", json={"question": "Projenin adı nedir?"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers.get("content-type", ""))
        body = res.text
        self.assertIn("data: ", body)
        self.assertIn('"type": "meta"', body)
        self.assertIn('"type": "chunk"', body)
        self.assertIn('"type": "done"', body)

    def test_10_frontend_static_serving(self):
        """Derlenmiş React üretim dosyalarının sunulma testi."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("<html", res.text.lower())

    def test_11_security_headers_and_sanitization(self):
        """Kurumsal güvenlik başlıkları ve sanitizasyon testi."""
        res = self.client.get("/api/health")
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(res.headers.get("X-XSS-Protection"), "1; mode=block")

        # Null byte sanitizasyonu testi
        res_null = self.client.post("/api/chat/stream", json={"question": "\x00\x00   \x00"})
        self.assertEqual(res_null.status_code, 200)
        self.assertIn("Lütfen geçerli bir soru yazın", res_null.text)

    def test_12_offline_whisper_transcription(self):
        """Yerel Whisper ses transkripsiyon API uç nokta testi."""
        # Boş / geçersiz ses dosyası kontrolü
        res_empty = self.client.post(
            "/api/speech/transcribe",
            files={"audio_file": ("test.webm", b"short_dummy_audio_bytes", "audio/webm")}
        )
        self.assertEqual(res_empty.status_code, 200)
        data = res_empty.json()
        self.assertIn("text", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
