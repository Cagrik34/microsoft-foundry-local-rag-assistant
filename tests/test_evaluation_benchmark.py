"""
RAG Kalite ve Doğruluk Benchmark Testi (tests/test_evaluation_benchmark.py)
=============================================================================
Değerlendirme veri seti üzerinde otomatik RAG kalite metriklerini ölçer.
"""

import os
import sys
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

from src.core.models import ModelManager
from src.core.database import VectorDatabase
from src.core.engine import RAGEngine
from src.core.evaluator import RAGEvaluator, EvaluationSample


class TestRAGEvaluationBenchmark(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*70)
        print("  📊 ZENITH AI — RAG KALİTE & DOĞRULUK BENCHMARK TESTİ")
        print("="*70)
        cls.models = ModelManager()
        cls.models.initialize()
        cls.models.load_embedding_model()
        cls.models.load_chat_model()
        cls.db = VectorDatabase()
        cls.engine = RAGEngine(cls.models, cls.db)
        cls.evaluator = RAGEvaluator(cls.engine)

        # Belgelerin indeksli olduğundan emin ol
        if cls.db.get_chunk_count() == 0:
            print("📂 Test öncesi dokümanlar indeksleniyor...")
            cls.engine.ingest_documents()

    @classmethod
    def tearDownClass(cls):
        print("\n" + "="*70)
        print("  🧹 Benchmark tamamlandı, modeller bellekten boşaltılıyor...")
        cls.models.shutdown()
        print("="*70 + "\n")

    def test_run_comprehensive_benchmark(self):
        """Altın test seti üzerinde RAG performansını değerlendirir."""
        benchmark_dataset = [
            EvaluationSample(
                question="CodePulse projesinin toplam bütçesi ne kadardır?",
                ground_truth_keywords=["2.340.000", "bütçe", "TL"]
            ),
            EvaluationSample(
                question="CodePulse platformunda hangi kod analiz modeli ve veritabanı kullanılmaktadır?",
                ground_truth_keywords=["CodeLlama", "PostgreSQL"]
            ),
            EvaluationSample(
                question="CodePulse platformu hangi programlama dillerini desteklemektedir?",
                ground_truth_keywords=["Python", "TypeScript", "Go", "Rust"]
            ),
            EvaluationSample(
                question="Mars gezegenindeki su kaynakları ve madencilik faaliyetleri nelerdir?",
                ground_truth_keywords=["yer almamaktadır"]
            )
        ]

        report = self.evaluator.run_benchmark(benchmark_dataset)

        print("\n" + "-"*70)
        print(f"  📈 TOPLAM SKOR (Composite Quality Score): %{report['composite_score_percent']}")
        print(f"  🎯 Faithfulness (Sadakat / Halüsinasyonsuzluk): %{report['avg_faithfulness_percent']}")
        print(f"  📌 Groundedness (Alıntı Geçerliliği): %{report['avg_groundedness_percent']}")
        print(f"  🔍 Keyword Recall (Anahtar Terim Kapsama): %{report['avg_keyword_recall_percent']}")
        print(f"  ⚡ Ortalama Arama Gecikmesi: {report['avg_search_latency_sec']}s")
        print(f"  ⏱️ Ortalama Üretim Gecikmesi: {report['avg_gen_latency_sec']}s")
        print("-"*70)

        # Temel kalite eşik kontrolleri
        self.assertGreaterEqual(report['composite_score_percent'], 70.0, "Genel RAG skor eşiği %70 olmalıdır.")
        self.assertGreaterEqual(report['avg_groundedness_percent'], 60.0, "Alıntı sadakati %60 üzerinde olmalıdır.")
        self.assertLessEqual(report['avg_search_latency_sec'], 3.0, "Arama süresi 3 saniyeden kısa olmalıdır.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
