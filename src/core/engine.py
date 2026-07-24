"""
RAG Orkestrasyon Motoru (src/core/engine.py)
==============================================
Tüm RAG akışını, sorgulamayı, bağlam oluşturmayı ve dosya özetlemeyi yönetir.
"""

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
    """Tüm RAG akışını koordine eden ana motor sınıfı."""

    def __init__(self, model_manager: ModelManager, database: VectorDatabase):
        self.models = model_manager
        self.db = database

    def ingest_documents(self, directory: Optional[str] = None) -> dict:
        """Belgeleri okur, vektörleştirir ve SQLite veritabanına kaydeder."""
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
            print(f"   🧠 {doc.file_name}: {len(texts)} chunk vektörleştiriliyor...")
            try:
                embeddings = self.models.generate_embeddings_batch(texts)
            except Exception:
                embeddings = [self.models.generate_embedding(t) for t in texts]

            records = [(c.source_file, c.chunk_index, c.content, emb) for c, emb in zip(doc.chunks, embeddings)]
            saved = self.db.store_chunks_batch(records)
            total += saved
            file_results.append({"file": doc.file_name, "chunks": saved})

        print(f"\n💾 Toplam {total} chunk veritabanına kaydedildi.")
        return {"total_files": len(file_results), "total_chunks": total, "files": file_results}

    def query_stream(self, question: str, top_k: int = TOP_K) -> Tuple[Iterator[str], List[SearchResult], str, float]:
        """Kullanıcı sorusunu alır, arama yapar ve (stream_generator, sources, context, search_time) döner."""
        if not self.models.is_embedding_ready:
            self.models.load_embedding_model()
        if not self.models.is_chat_ready:
            self.models.load_chat_model()

        if self._is_summary_query(question):
            t_search_start = time.time()
            files = self.db.get_indexed_files()
            search_time = round(time.time() - t_search_start, 2)
            res = self._summarize_per_file()
            def text_gen():
                words = res.answer.split(" ")
                for i, w in enumerate(words):
                    yield w + (" " if i < len(words) - 1 else "")
                    time.sleep(0.008)
            return text_gen(), res.sources, res.context_used, search_time

        t_search_start = time.time()
        q_emb = self.models.generate_embedding(question)
        results = self.db.search(q_emb, top_k=top_k)
        search_time = round(time.time() - t_search_start, 2)

        if not results:
            def empty_gen():
                yield "Veritabanında ilgili belge bulunamadı."
            return empty_gen(), [], "", search_time

        context = self._format_context(results)
        context = self._truncate_context(context, MAX_CONTEXT_CHARS)

        is_english = any(w in question.lower().split() for w in ["what", "how", "why", "explain", "where", "the"])
        sys_prompt = SYSTEM_PROMPT_EN.format(context=context) if is_english else SYSTEM_PROMPT.format(context=context)

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question},
        ]
        full_text = self.models.chat_complete(messages)
        full_text = self._clean_thinking_tags(full_text)

        def word_stream():
            import re
            words = full_text.split(" ")
            for i, w in enumerate(words):
                if re.search(r'[\u4e00-\u9fff]', w):
                    continue
                yield w + (" " if i < len(words) - 1 else "")
                time.sleep(0.012)

        return word_stream(), results, context, search_time

    def query(self, question: str, top_k: int = TOP_K) -> RAGResponse:
        """Kullanıcı sorusunu alır, vektör araması yapar ve tek parça LLM yanıtı üretir."""
        if not self.models.is_embedding_ready:
            self.models.load_embedding_model()
        if not self.models.is_chat_ready:
            self.models.load_chat_model()

        if self._is_summary_query(question):
            return self._summarize_per_file()

        q_emb = self.models.generate_embedding(question)
        results = self.db.search(q_emb, top_k=top_k)

        if not results:
            return RAGResponse("Veritabanında ilgili belge bulunamadı.", [], "")

        context = self._format_context(results)
        context = self._truncate_context(context, MAX_CONTEXT_CHARS)

        is_english = any(w in question.lower().split() for w in ["what", "how", "why", "explain", "where", "the"])
        sys_prompt = SYSTEM_PROMPT_EN.format(context=context) if is_english else SYSTEM_PROMPT.format(context=context)

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": question},
        ]
        answer = self.models.chat_complete(messages)
        answer = self._clean_thinking_tags(answer)
        return RAGResponse(answer=answer, sources=results, context_used=context)

    @staticmethod
    def _clean_thinking_tags(text: str) -> str:
        """Model yanıtındaki <think>...</think> bloklarını ve Çince sistem prefix'lerini temizler."""
        if not text:
            return text
        import re
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        cleaned = re.sub(r'[\u4e00-\u9fff]+[^\n]*', '', cleaned).strip()
        return cleaned if cleaned else text.strip()

    @staticmethod
    def _is_summary_query(question: str) -> bool:
        """Sorunun genel özet talebi olup olmadığını kontrol eder."""
        q = question.lower()
        kws = ["özetle", "özet", "ozetle", "ozet", "tüm dosya", "hepsini", "ne içeriyor", "summarize", "summary", "overview"]
        return any(kw in q for kw in kws)

    def _summarize_per_file(self) -> RAGResponse:
        """Tüm dosyaları bağımsız olarak özetler ve birleştirir (Halüsinasyon engelleme)."""
        files = self.db.get_indexed_files()
        if not files:
            return RAGResponse("Veritabanında belge bulunamadı.", [], "")

        summaries, sources = [], []
        for f_name in files:
            chunks = self.db.get_chunks_by_file(f_name, limit=3)
            if not chunks:
                continue
            ctx = self._truncate_context("\n\n".join(chunks), MAX_CONTEXT_CHARS)
            msgs = [
                {"role": "system", "content": SYSTEM_PROMPT_SUMMARIZE.format(context=ctx)},
                {"role": "user", "content": f'"{f_name}" dosyasını kısaca özetle.'}
            ]
            summary = self.models.chat_complete(msgs)
            summaries.append(f"**{f_name}:**\n{summary.strip()}")
            sources.append(SearchResult(content=chunks[0], source_file=f_name, chunk_index=0, similarity=1.0))

        return RAGResponse("\n\n".join(summaries), sources, "[Dosya bazlı özet]")

    @staticmethod
    def _format_context(results: List[SearchResult]) -> str:
        """Arama sonuçlarını metin bağlamına formatlar."""
        return "\n".join([
            CONTEXT_CHUNK_TEMPLATE.format(source=r.source_file, index=r.chunk_index + 1, content=r.content)
            for r in results
        ])

    @staticmethod
    def _truncate_context(context: str, max_chars: int) -> str:
        """Bağlam metnini sınırın altına kısaltır."""
        if len(context) <= max_chars:
            return context
        trunc = context[:max_chars]
        newline = trunc.rfind("\n")
        if newline > max_chars // 2:
            trunc = trunc[:newline]
        return trunc + "\n\n[Not: Bağlam sınırı nedeniyle kısaltıldı.]"
