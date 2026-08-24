"""
Zenith AI CI Pipeline Unit Tests (tests/test_ci_pipeline.py)
=============================================================
Automated test suite designed for GitHub Actions CI/CD pipeline and local execution.
Tests document loaders, SQLite FTS5 BM25 search, RRF scoring, RAG evaluation metrics,
and FastAPI REST endpoints.
"""

import os
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from starlette.testclient import TestClient
from src.core.document_loader import chunk_text, read_document
from src.core.database import VectorDatabase
from src.core.evaluator import EvaluationSample, EvaluationMetricResult, RAGEvaluator
from src.core.models import SearchResult, RAGResponse
from src.api.server import app


class TestZenithAICIPipeline(unittest.TestCase):

    def test_01_chunking_algorithm(self):
        sample_text = "=== Bolum 1 ===\n" + ("Paragraf 1 metni. " * 50) + "\n\n=== Bolum 2 ===\n" + ("Paragraf 2 metni. " * 40)
        chunks = chunk_text(sample_text)
        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(len(c) > 0 for c in chunks))

    def test_02_sqlite_fts5_database_operations(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            db = VectorDatabase(db_path=db_path)
            self.assertEqual(db.get_chunk_count(), 0)

            # Insert test chunks: (source_file, chunk_index, content, embedding)
            dummy_vector = [0.05] * 1024
            test_records = [
                ("belge1.md", 0, "Zenith AI yerel donanimda calisan bir RAG asistanidir.", dummy_vector),
                ("belge2.md", 0, "Microsoft Foundry Local SDK ile phi-4-mini modeli entegre edilmistir.", dummy_vector),
                ("belge3.md", 0, "Finansal veriler ve TEFAS fonlari analiz edilebilir.", dummy_vector)
            ]

            inserted = db.store_chunks_batch(test_records)
            self.assertEqual(inserted, 3)
            self.assertEqual(db.get_chunk_count(), 3)

            # FTS5 BM25 Keyword Search
            bm25_results = db.search_bm25("Foundry Local phi-4-mini", top_k=2)
            self.assertGreater(len(bm25_results), 0)
            self.assertIn("phi-4-mini", bm25_results[0].content)

            # Session Operations
            sess_id = db.create_session("Test Oturumu")
            self.assertGreater(len(sess_id), 0)
            sessions = db.get_sessions()
            self.assertTrue(any(s.session_id == sess_id for s in sessions))

            db.delete_session(sess_id)
            sessions_after = db.get_sessions()
            self.assertFalse(any(s.session_id == sess_id for s in sessions_after))
        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except Exception:
                    pass

    def test_03_rag_evaluation_metric_computations(self):
        class MockRAGEngine:
            def query_search(self, q):
                return [SearchResult("Test icerik", "belge.md", 0, 0.85, 1, "hybrid")], "Test baglam", 0.12
            def query(self, q):
                return RAGResponse(
                    answer="CodePulse projesinin toplam butcesi 2.340.000 TL olarak belirlenmistir [1].",
                    sources=[SearchResult("Test icerik", "belge.md", 0, 0.85, 1, "hybrid")],
                    context_used="Test baglam"
                )

        evaluator = RAGEvaluator(MockRAGEngine())
        sample = EvaluationSample(
            question="CodePulse projesinin toplam butcesi ne kadardir?",
            ground_truth_keywords=["2.340.000", "butce", "TL"]
        )
        result = evaluator.evaluate_sample(sample)

        self.assertGreater(result.keyword_recall_score, 0.5)
        self.assertEqual(result.groundedness_score, 1.0)
        self.assertGreater(result.faithfulness_score, 0.8)

    def test_04_fastapi_rest_endpoints(self):
        client = TestClient(app)

        # Health Check
        res_health = client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)

        # Database Stats
        res_stats = client.get("/api/stats")
        self.assertEqual(res_stats.status_code, 200)
        self.assertIn("total_chunks", res_stats.json())

        # Session Management Lifecycle
        res_create = client.post("/api/sessions", json={"title": "CI Test Session"})
        self.assertEqual(res_create.status_code, 200)
        sess_id = res_create.json()["session_id"]

        res_list = client.get("/api/sessions")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(s["session_id"] == sess_id for s in res_list.json()))

        res_del = client.delete(f"/api/sessions/{sess_id}")
        self.assertEqual(res_del.status_code, 200)


if __name__ == "__main__":
    unittest.main()