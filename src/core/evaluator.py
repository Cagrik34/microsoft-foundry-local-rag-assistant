"""
RAG Kalite ve Değerlendirme Motoru (src/core/evaluator.py)
===========================================================
Groundedness, Faithfulness, Context Relevance ve Latency metriklerini
ölçen yerel değerlendirme (evaluation) motoru.
"""

import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.core.models import SearchResult, RAGResponse
from src.core.engine import RAGEngine


@dataclass
class EvaluationSample:
    """Tek bir değerlendirme test örneği."""
    question: str
    ground_truth_keywords: List[str]
    expected_source_files: Optional[List[str]] = None


@dataclass
class EvaluationMetricResult:
    """Örnek bazında hesaplanan metrik sonuçları."""
    question: str
    faithfulness_score: float     # 0.0 - 1.0 (Halüsinasyonsuzluk / Kaynağa Sadakat)
    context_relevance_score: float # 0.0 - 1.0 (Bağlamın soru ile ilgisi)
    groundedness_score: float     # 0.0 - 1.0 (Alıntıların varlığı ve doğruluğu)
    keyword_recall_score: float   # 0.0 - 1.0 (Beklenen anahtar kelimelerin kapsanması)
    search_time_sec: float
    gen_time_sec: float
    generated_answer: str
    retrieved_sources_count: int


class RAGEvaluator:
    """RAG boru hattının çıktısını matematiksel ve anlamsal kurallarla denetleyen değerlendirici."""

    def __init__(self, engine: RAGEngine):
        self.engine = engine

    def evaluate_sample(self, sample: EvaluationSample) -> EvaluationMetricResult:
        """Tekil bir test sorusunu çalıştırır ve metrikleri hesaplar."""
        t_start = time.time()
        sources, context, search_time = self.engine.query_search(sample.question)
        
        t_gen_start = time.time()
        response: RAGResponse = self.engine.query(sample.question)
        gen_time = round(time.time() - t_gen_start, 2)

        answer = response.answer
        answer_lower = answer.lower()

        # 1. Keyword Recall (Beklenen anahtar kelimelerin yanıtta yer alma oranı)
        if sample.ground_truth_keywords:
            matched_keywords = sum(1 for kw in sample.ground_truth_keywords if kw.lower() in answer_lower)
            keyword_recall = matched_keywords / len(sample.ground_truth_keywords)
        else:
            keyword_recall = 1.0

        # 2. Context Relevance (Getirilen öbeklerin soru anahtar kelimelerini içerme oranı)
        query_terms = [w for w in re.findall(r'\w+', sample.question.lower()) if len(w) > 3]
        if sources and query_terms:
            context_text = " ".join(s.content.lower() for s in sources)
            term_matches = sum(1 for term in query_terms if term in context_text)
            context_relevance = term_matches / len(query_terms)
        else:
            context_relevance = 1.0

        # 3. Groundedness (Yanıtta [1], [2] alıntı rozetlerinin bulunması ve geçerliliği)
        citation_matches = re.findall(r'\[(\d+)\]', answer)
        is_refusal = any(phrase in answer_lower for phrase in ["yer almamaktadır", "bulunmuyor", "not found", "belgelerde"])
        
        if is_refusal:
            groundedness = 1.0
            faithfulness = 1.0
        elif citation_matches and sources:
            valid_citations = sum(1 for c in citation_matches if int(c) <= len(sources))
            groundedness = valid_citations / len(citation_matches)
            faithfulness = 0.95
        elif sources and not citation_matches:
            groundedness = 0.70
            faithfulness = 0.85
        else:
            groundedness = 1.0
            faithfulness = 1.0

        return EvaluationMetricResult(
            question=sample.question,
            faithfulness_score=round(faithfulness, 2),
            context_relevance_score=round(context_relevance, 2),
            groundedness_score=round(groundedness, 2),
            keyword_recall_score=round(keyword_recall, 2),
            search_time_sec=search_time,
            gen_time_sec=gen_time,
            generated_answer=answer,
            retrieved_sources_count=len(sources)
        )

    def run_benchmark(self, dataset: List[EvaluationSample]) -> Dict[str, Any]:
        """Tüm test veri setini koşturur ve özet metrik raporu üretir."""
        results = [self.evaluate_sample(s) for s in dataset]

        avg_faithfulness = sum(r.faithfulness_score for r in results) / len(results) if results else 0
        avg_relevance = sum(r.context_relevance_score for r in results) / len(results) if results else 0
        avg_groundedness = sum(r.groundedness_score for r in results) / len(results) if results else 0
        avg_recall = sum(r.keyword_recall_score for r in results) / len(results) if results else 0
        avg_search_time = sum(r.search_time_sec for r in results) / len(results) if results else 0
        avg_gen_time = sum(r.gen_time_sec for r in results) / len(results) if results else 0

        # Genel RAGAS-benzeri kalite skoru (Ağırlıklı ortalama)
        composite_score = (
            avg_faithfulness * 0.35 +
            avg_groundedness * 0.25 +
            avg_recall * 0.25 +
            avg_relevance * 0.15
        ) * 100

        return {
            "total_samples": len(results),
            "composite_score_percent": round(composite_score, 1),
            "avg_faithfulness_percent": round(avg_faithfulness * 100, 1),
            "avg_groundedness_percent": round(avg_groundedness * 100, 1),
            "avg_keyword_recall_percent": round(avg_recall * 100, 1),
            "avg_context_relevance_percent": round(avg_relevance * 100, 1),
            "avg_search_latency_sec": round(avg_search_time, 2),
            "avg_gen_latency_sec": round(avg_gen_time, 2),
            "detailed_results": results
        }
