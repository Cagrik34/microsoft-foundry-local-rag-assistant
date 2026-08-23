"""
RAG Orkestrasyon Motoru (src/core/engine.py)
==============================================
Hibrit Arama (Dense + BM25 RRF), Metin İçi Alıntı Entegrasyonu ([1], [2]) ve Çok Turlu Bağlam Yönetimi.
"""

import re
import time
from typing import List, Optional, Tuple, Iterator
from src.config import (
    TOP_K, MAX_CONTEXT_CHARS, SYSTEM_PROMPT, SYSTEM_PROMPT_EN,
    SYSTEM_PROMPT_SUMMARIZE, CONTEXT_CHUNK_TEMPLATE
)
from src.core.models import ModelManager, SearchResult, RAGResponse
from src.core.database import VectorDatabase
from src.core.document_loader import process_all_documents


class RAGEngine:
    """Tüm RAG akışını, hibrit arama koordinasyonunu ve model çıkarımını yöneten ana motor."""

    def __init__(self, model_manager: ModelManager, database: VectorDatabase):
        self.models = model_manager
        self.db = database

    def ingest_documents(self, directory: Optional[str] = None) -> dict:
        """Belgeleri okur, vektörleştirir ve hem Vektör hem FTS5 BM25 tablosuna kaydeder."""
        if not self.models.is_embedding_ready:
            self.models.load_embedding_model()

        print("📂 Belgeler taranıyor ve işleniyor...")
        docs = process_all_documents(directory) if directory else process_all_documents()
        if not docs:
            return {"total_files": 0, "total_chunks": 0, "files": []}

        total = 0
        file_results = []
        for doc in docs:
            if not doc.chunks:
                continue
            texts = [c.content for c in doc.chunks]
            print(f"   🧠 {doc.file_name}: {len(texts)} öbek vektörleştiriliyor...")
            try:
                embeddings = self.models.generate_embeddings_batch(texts)
            except Exception:
                embeddings = [self.models.generate_embedding(t) for t in texts]

            records = [(c.source_file, c.chunk_index, c.content, emb) for c, emb in zip(doc.chunks, embeddings)]
            saved = self.db.store_chunks_batch(records)
            total += saved
            file_results.append({"file": doc.file_name, "chunks": saved})

        print(f"\n💾 Toplam {total} öbek veritabanına ve FTS5 indeksine kaydedildi.")
        return {"total_files": len(file_results), "total_chunks": total, "files": file_results}

    def query_search(self, question: str, top_k: int = TOP_K) -> Tuple[List[SearchResult], str, float]:
        """Kullanıcı sorusunu alır, Hibrit Arama (Dense + BM25 RRF) yapar ve (sources, context, search_time) döner."""
        if not self.models.is_embedding_ready:
            self.models.load_embedding_model()

        if self._is_summary_query(question):
            t_search_start = time.time()
            files = self.db.get_indexed_files()
            search_time = round(time.time() - t_search_start, 2)
            return [], "[SUMMARY]", search_time

        t_search_start = time.time()
        q_emb = self.models.generate_embedding(question)
        # Hibrit Arama: Dense Kosinüs + FTS5 BM25 + RRF
        results = self.db.search_hybrid(query_text=question, query_embedding=q_emb, top_k=top_k)
        search_time = round(time.time() - t_search_start, 2)

        if not results:
            return [], "", search_time

        context = self._format_context(results)
        context = self._truncate_context(context, MAX_CONTEXT_CHARS)
        return results, context, search_time

    def query_generate(
        self,
        question: str,
        sources: List[SearchResult],
        context: str,
        chat_history: Optional[List[dict]] = None
    ) -> Iterator[str]:
        """Arama sonuçları, alıntılar ve isteğe bağlı çok turlu sohbet hafızası ile LLM akışı üretir."""
        if not self.models.is_chat_ready:
            self.models.load_chat_model()

        if context == "[SUMMARY]":
            res = self._summarize_per_file()
            def text_gen():
                words = res.answer.split(" ")
                for i, w in enumerate(words):
                    yield w + (" " if i < len(words) - 1 else "")
                    time.sleep(0.006)
            return text_gen()

        if not sources:
            def empty_gen():
                yield "Bu bilgi indekslenmiş belgelerde bulunmuyor."
            return empty_gen()

        is_english = any(w in re.findall(r'\b\w+\b', question.lower()) for w in ["what", "how", "why", "explain", "where", "the"])
        sys_prompt = SYSTEM_PROMPT_EN.format(context=context) if is_english else SYSTEM_PROMPT.format(context=context)

        messages = [{"role": "system", "content": sys_prompt}]

        # Çok turlu hafıza desteği (Yalnızca önceki konuşma turları)
        if chat_history:
            prior_turns = [t for t in chat_history if t.get("role") in ("user", "assistant") and t.get("content") and t.get("content") != question]
            for turn in prior_turns[-4:]:
                messages.append({"role": turn["role"], "content": turn["content"]})

        # Mevcut soru
        messages.append({"role": "user", "content": question})

        full_text = self.models.chat_complete(messages)
        full_text = self._clean_thinking_tags(full_text)

        def word_stream():
            words = full_text.split(" ")
            for i, w in enumerate(words):
                yield w + (" " if i < len(words) - 1 else "")
                time.sleep(0.003)

        return word_stream()

    def query_stream(self, question: str, top_k: int = TOP_K) -> Tuple[Iterator[str], List[SearchResult], str, float]:
        """CLI uyumluluğu için tekil akış arayüzü."""
        sources, context, search_time = self.query_search(question, top_k=top_k)
        stream_gen = self.query_generate(question, sources, context)
        return stream_gen, sources, context, search_time

    def query(self, question: str, top_k: int = TOP_K) -> RAGResponse:
        """Kullanıcı sorusunu alır, hibrit arama yapar ve tek parça LLM yanıtı üretir."""
        sources, context, _ = self.query_search(question, top_k=top_k)
        if context == "[SUMMARY]":
            return self._summarize_per_file()
        if not sources:
            return RAGResponse("Bu bilgi belgelerde bulunmuyor.", [], "")

        is_english = any(w in re.findall(r'\b\w+\b', question.lower()) for w in ["what", "how", "why", "explain", "where", "the"])
        sys_prompt = SYSTEM_PROMPT_EN.format(context=context) if is_english else SYSTEM_PROMPT.format(context=context)

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question},
        ]
        answer = self.models.chat_complete(messages)
        answer = self._clean_thinking_tags(answer)
        return RAGResponse(answer=answer, sources=sources, context_used=context)

    @staticmethod
    def _clean_thinking_tags(text: str) -> str:
        """Model yanıtındaki düşünme bloklarını temizler."""
        if not text:
            return text
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        cleaned = re.sub(r'[\u4e00-\u9fff]+[^\n]*', '', cleaned).strip()
        return cleaned if cleaned else text.strip()

    @staticmethod
    def _is_summary_query(question: str) -> bool:
        """Sorunun genel özet talebi olup olmadığını kontrol eder."""
        q = question.lower().strip()
        general_patterns = [
            r'^(tüm|bütün|hepsini|her \u015feyi).*(özetle|özet)',
            r'^(özetle|özet ver|genel özet)',
            r'(tüm dosya|bütün belge|hepsini özetle)',
            r'^(ne içeriyor|neler var|içeriği ne)',
            r'^(summarize|summary|overview)$',
            r'^(summarize|give.*summary|overview).*(all|document|everything)',
        ]
        return any(re.search(p, q) for p in general_patterns)

    def _summarize_per_file(self) -> RAGResponse:
        """Tüm dosyaları tek bir LLM çağrısıyla özetler."""
        files = self.db.get_indexed_files()
        if not files:
            return RAGResponse("Veritabanında belge bulunamadı.", [], "")

        all_snippets = []
        sources = []
        for i, f_name in enumerate(files[:6]):
            chunks = self.db.get_chunks_by_file(f_name, limit=2)
            if not chunks:
                continue
            snippet = "\n".join(chunks)[:400]
            all_snippets.append(f"[Kaynak {i+1}: {f_name}]:\n{snippet}")
            sources.append(SearchResult(
                content=chunks[0],
                source_file=f_name,
                chunk_index=0,
                similarity=1.0,
                citation_index=i+1,
                match_type="summary"
            ))

        combined_context = "\n\n".join(all_snippets)
        combined_context = self._truncate_context(combined_context, MAX_CONTEXT_CHARS)

        msgs = [
            {"role": "system", "content": SYSTEM_PROMPT_SUMMARIZE.format(context=combined_context)},
            {"role": "user", "content": "Yukarıdaki tüm belgelerin ana temalarını dosya dosya kısaca özetle."}
        ]
        summary = self.models.chat_complete(msgs)
        summary = self._clean_thinking_tags(summary)
        return RAGResponse(summary.strip(), sources, "[Birleşik Belge Özeti]")

    @staticmethod
    def _format_context(results: List[SearchResult]) -> str:
        """Arama sonuçlarını numaralandırılmış [Kaynak 1], [Kaynak 2] metin bağlamına formatlar."""
        return "\n".join([
            CONTEXT_CHUNK_TEMPLATE.format(
                num=r.citation_index,
                source=r.source_file,
                index=r.chunk_index + 1,
                content=r.content
            )
            for r in results
        ])

    @staticmethod
    def _truncate_context(context: str, max_chars: int) -> str:
        """Bağlam metnini sınırın altına güvenle kısaltır."""
        if len(context) <= max_chars:
            return context
        trunc = context[:max_chars]
        newline = trunc.rfind("\n")
        if newline > max_chars // 2:
            trunc = trunc[:newline]
        return trunc + "\n\n[Not: Bağlam sınırı nedeniyle kısaltıldı.]"
