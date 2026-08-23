"""
SQLite Hibrit Vektör & FTS5 Veritabanı Modülü (src/core/database.py)
====================================================================
Yoğun Vektör Arama (Dense) + Tam Metin BM25 Arama (FTS5) + Reciprocal Rank Fusion (RRF)
ve Çoklu Sohbet Oturumu (Session Memory) Yönetimi.
"""

import os
import re
import json
import sqlite3
import uuid
from typing import List, Tuple, Optional, Dict
import numpy as np
from src.config import (
    DB_PATH, TOP_K, SIMILARITY_THRESHOLD, MAX_CHUNKS_PER_FILE,
    HYBRID_ALPHA, RRF_K
)
from src.core.models import SearchResult, ChatMessage, ChatSession


class VectorDatabase:
    """SQLite tabanlı hibrit vektör ve tam metin deposu ile oturum yöneticisi."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """SQLite bağlantısı döner."""
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        """Veritabanı tablolarını, FTS5 tam metin indeksini ve oturum tablolarını oluşturur."""
        with self._connect() as conn:
            # 1. Ana Vektör Tablosu
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_file TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_file, chunk_index)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON documents(source_file)")

            # 2. SQLite FTS5 Tam Metin (BM25) Arama Sanal Tablosu
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    content,
                    source_file UNINDEXED,
                    chunk_index UNINDEXED,
                    tokenize='unicode61'
                )
            """)

            # 3. Sohbet Oturumları Tablosu (Multi-Session Management)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 4. Sohbet Mesajları Tablosu
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources_json TEXT DEFAULT '',
                    search_time REAL DEFAULT 0.0,
                    gen_time REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON chat_messages(session_id)")
            conn.commit()

    def store_chunks_batch(self, records: List[Tuple[str, int, str, List[float]]]) -> int:
        """Metin öbeklerini ve normalize edilmiş vektörlerini hem 'documents' hem 'documents_fts' tablolarına kaydeder."""
        source_files = set(src for src, _, _, _ in records)
        rows_doc = []
        rows_fts = []

        for src, idx, txt, emb in records:
            vec = np.array(emb, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            rows_doc.append((src, idx, txt, vec.tobytes()))
            rows_fts.append((txt, src, str(idx)))

        with self._connect() as conn:
            # Eski kayıtları temizle
            for sf in source_files:
                conn.execute("DELETE FROM documents WHERE source_file = ?", (sf,))
                conn.execute("DELETE FROM documents_fts WHERE source_file = ?", (sf,))

            # Vektör tablosuna ekle
            conn.executemany("""
                INSERT INTO documents (source_file, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?)
            """, rows_doc)

            # FTS5 tablosuna ekle
            conn.executemany("""
                INSERT INTO documents_fts (content, source_file, chunk_index)
                VALUES (?, ?, ?)
            """, rows_fts)

            conn.commit()
        return len(rows_doc)

    def search_vector(self, query_embedding: List[float], top_k: int = TOP_K * 2) -> List[SearchResult]:
        """Yoğun vektör kosinüs benzerliği araması."""
        with self._connect() as conn:
            rows = conn.execute("SELECT id, source_file, chunk_index, content, embedding FROM documents").fetchall()

        if not rows:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        sources, indices, contents, embeddings = [], [], [], []
        for _id, src, idx, txt, emb_blob in rows:
            vec = np.frombuffer(emb_blob, dtype=np.float32)
            if np.linalg.norm(vec) == 0:
                continue
            embeddings.append(vec)
            sources.append(src)
            indices.append(idx)
            contents.append(txt)

        if not embeddings:
            return []

        matrix = np.stack(embeddings)
        sims = matrix @ q_vec

        scored = [(sim, i) for i, sim in enumerate(sims) if sim >= SIMILARITY_THRESHOLD]
        scored.sort(key=lambda x: x[0], reverse=True)

        results: List[SearchResult] = []
        for rank, (sim, i) in enumerate(scored[:top_k]):
            results.append(SearchResult(
                content=contents[i],
                source_file=sources[i],
                chunk_index=indices[i],
                similarity=float(sim),
                citation_index=rank + 1,
                match_type="vector"
            ))
        return results

    def search_bm25(self, query_text: str, top_k: int = TOP_K * 2) -> List[SearchResult]:
        """SQLite FTS5 BM25 tam metin kelime araması."""
        clean_query = re.sub(r'[^\w\s]', ' ', query_text).strip()
        tokens = [w for w in clean_query.split() if len(w) > 1]
        if not tokens:
            return []

        # FTS5 OR sorgusu oluştur
        fts_match_expr = " OR ".join(f'"{t}"' for t in tokens[:10])

        with self._connect() as conn:
            try:
                rows = conn.execute("""
                    SELECT content, source_file, chunk_index, rank
                    FROM documents_fts
                    WHERE documents_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_match_expr, top_k)).fetchall()
            except Exception:
                return []

        results: List[SearchResult] = []
        for rank, (txt, src, idx_str, bm25_rank) in enumerate(rows):
            # FTS5 rank değeri negatif döner (daha küçük = daha iyi), 0-1 aralığına normalize et
            sim_score = max(0.1, min(0.95, 1.0 / (1.0 + abs(float(bm25_rank)))))
            results.append(SearchResult(
                content=txt,
                source_file=src,
                chunk_index=int(idx_str),
                similarity=sim_score,
                citation_index=rank + 1,
                match_type="bm25"
            ))
        return results

    def search_hybrid(
        self,
        query_text: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = TOP_K,
        alpha: float = HYBRID_ALPHA,
        rrf_k: int = RRF_K
    ) -> List[SearchResult]:
        """Vektör (Dense) ve BM25 (Lexical) aramalarını Reciprocal Rank Fusion (RRF) ile birleştirir."""
        dense_results = self.search_vector(query_embedding, top_k=top_k * 3) if query_embedding else []
        bm25_results = self.search_bm25(query_text, top_k=top_k * 3) if query_text else []

        if not dense_results and not bm25_results:
            return []
        if not bm25_results:
            return self._finalize_results(dense_results, top_k)
        if not dense_results:
            return self._finalize_results(bm25_results, top_k)

        # RRF Puanlama Tablosu
        rrf_scores: Dict[Tuple[str, int], float] = {}
        content_map: Dict[Tuple[str, int], str] = {}
        raw_sim_map: Dict[Tuple[str, int], float] = {}
        match_type_map: Dict[Tuple[str, int], str] = {}

        # 1. Dense Vektör Sıralama Katkısı
        for rank, res in enumerate(dense_results):
            key = (res.source_file, res.chunk_index)
            score = alpha * (1.0 / (rrf_k + rank + 1))
            rrf_scores[key] = rrf_scores.get(key, 0.0) + score
            content_map[key] = res.content
            raw_sim_map[key] = res.similarity
            match_type_map[key] = "vector"

        # 2. BM25 Sıralama Katkısı
        for rank, res in enumerate(bm25_results):
            key = (res.source_file, res.chunk_index)
            score = (1.0 - alpha) * (1.0 / (rrf_k + rank + 1))
            rrf_scores[key] = rrf_scores.get(key, 0.0) + score
            content_map[key] = res.content
            if key in raw_sim_map:
                raw_sim_map[key] = max(raw_sim_map[key], res.similarity)
                match_type_map[key] = "hybrid"  # Hem vektör hem BM25 eşleşti
            else:
                raw_sim_map[key] = res.similarity
                match_type_map[key] = "bm25"

        # RRF skoruna göre sırala
        sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

        final_candidates: List[SearchResult] = []
        for key in sorted_keys:
            src, idx = key
            final_candidates.append(SearchResult(
                content=content_map[key],
                source_file=src,
                chunk_index=idx,
                similarity=raw_sim_map[key],
                citation_index=1,
                match_type=match_type_map[key]
            ))

        return self._finalize_results(final_candidates, top_k)

    def _finalize_results(self, candidates: List[SearchResult], top_k: int) -> List[SearchResult]:
        """Kaynak çeşitliliği kuralını uygular ve 1-tabanlı alıntı indekslerini (citation_index) atar."""
        results: List[SearchResult] = []
        added = set()
        file_counts = {}

        # 1. Pas: Dosya başına sınır
        for item in candidates:
            if len(results) >= top_k:
                break
            key = (item.source_file, item.chunk_index)
            if file_counts.get(item.source_file, 0) < MAX_CHUNKS_PER_FILE:
                item.citation_index = len(results) + 1
                results.append(item)
                file_counts[item.source_file] = file_counts.get(item.source_file, 0) + 1
                added.add(key)

        # 2. Pas: Eşik dolmadıysa tamamla
        if len(results) < top_k:
            for item in candidates:
                if len(results) >= top_k:
                    break
                key = (item.source_file, item.chunk_index)
                if key not in added:
                    item.citation_index = len(results) + 1
                    results.append(item)
                    added.add(key)

        return results

    def search(self, query_embedding: List[float], top_k: int = TOP_K) -> List[SearchResult]:
        """Geriye uyumluluk için standart vektör araması."""
        return self.search_vector(query_embedding, top_k=top_k)

    # ── Oturum ve Mesaj Yönetimi (Multi-Session Management) ──

    def create_session(self, title: str = "Yeni Doküman Analizi") -> str:
        """Yeni bir sohbet oturumu oluşturur ve ID'sini döner."""
        session_id = str(uuid.uuid4())[:8]
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO chat_sessions (session_id, title)
                VALUES (?, ?)
            """, (session_id, title))
            conn.commit()
        return session_id

    def get_sessions(self) -> List[ChatSession]:
        """Tüm kayıtlı sohbet oturumlarını en yeniden eskiye sıralı döner."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT session_id, title, created_at, updated_at
                FROM chat_sessions
                ORDER BY updated_at DESC
            """).fetchall()
        return [ChatSession(session_id=r[0], title=r[1], created_at=r[2], updated_at=r[3]) for r in rows]

    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Belirli bir oturuma ait tüm mesajları kronolojik sırayla döner."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT id, session_id, role, content, sources_json, search_time, gen_time, created_at
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,)).fetchall()
        return [
            ChatMessage(
                id=r[0], session_id=r[1], role=r[2], content=r[3],
                sources_json=r[4], search_time=r[5], gen_time=r[6], created_at=r[7]
            )
            for r in rows
        ]

    def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
        search_time: float = 0.0,
        gen_time: float = 0.0
    ) -> int:
        """Oturuma yeni mesaj ekler ve oturumun güncellenme tarihini yeniler."""
        sources_json = json.dumps(sources or [], ensure_ascii=False)
        with self._connect() as conn:
            # Oturum yoksa otomatik oluştur
            exists = conn.execute("SELECT 1 FROM chat_sessions WHERE session_id = ?", (session_id,)).fetchone()
            if not exists:
                title = content[:35] + "..." if len(content) > 35 else content
                conn.execute("INSERT INTO chat_sessions (session_id, title) VALUES (?, ?)", (session_id, title))

            cur = conn.execute("""
                INSERT INTO chat_messages (session_id, role, content, sources_json, search_time, gen_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, role, content, sources_json, search_time, gen_time))

            conn.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
            conn.commit()
            return cur.lastrowid

    def delete_session(self, session_id: str) -> None:
        """Bir sohbet oturumunu ve tüm mesajlarını siler."""
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
            conn.commit()

    # ── İstatistik ve Genel Veritabanı Metrikleri ──

    def get_indexed_files(self) -> List[str]:
        """İndekslenmiş benzersiz dosya adlarını döndürür."""
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT source_file FROM documents ORDER BY source_file").fetchall()
        return [r[0] for r in rows]

    def get_chunks_by_file(self, source_file: str, limit: int = 4) -> List[str]:
        """Belirli bir dosyaya ait öbekleri sırayla döndürür."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT content FROM documents WHERE source_file = ? ORDER BY chunk_index ASC LIMIT ?
            """, (source_file, limit)).fetchall()
        return [r[0] for r in rows]

    def get_chunk_count(self) -> int:
        """Toplam öbek sayısını döndürür."""
        with self._connect() as conn:
            r = conn.execute("SELECT COUNT(*) FROM documents").fetchone()
        return r[0] if r else 0

    def clear_all(self) -> int:
        """Tüm indekslenmiş doküman ve FTS verilerini temizler."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM documents")
            conn.execute("DELETE FROM documents_fts")
            conn.commit()
            return cur.rowcount

    def get_stats(self) -> dict:
        """Veritabanı boyut ve içerik istatistiklerini döndürür."""
        files = self.get_indexed_files()
        file_stats = []
        with self._connect() as conn:
            for f in files:
                c = conn.execute("SELECT COUNT(*) FROM documents WHERE source_file = ?", (f,)).fetchone()[0]
                file_stats.append({"name": f, "chunks": c})

        db_size = os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0.0
        return {
            "total_chunks": self.get_chunk_count(),
            "total_files": len(files),
            "files": file_stats,
            "db_size_mb": round(db_size, 2),
        }
