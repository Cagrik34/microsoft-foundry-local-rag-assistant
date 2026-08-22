"""
SQLite Vektör Veritabanı Modülü (src/core/database.py)
======================================================
SQLite tabanlı yerel vektör deposu ve kosinüs benzerliği arama sınıfı.
"""

import os
import sqlite3
from typing import List, Tuple
import numpy as np
from src.config import DB_PATH, TOP_K, SIMILARITY_THRESHOLD, MAX_CHUNKS_PER_FILE
from src.core.models import SearchResult


class VectorDatabase:
    """SQLite tabanlı yerel vektör deposu ve kosinüs benzerliği arama sınıfı."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """SQLite bağlantısı döner."""
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        """Veritabanı tablosunu ve indeksleri oluşturur."""
        with self._connect() as conn:
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
            conn.commit()

    def store_chunks_batch(self, records: List[Tuple[str, int, str, List[float]]]) -> int:
        """Birden fazla metin öbeğini ve vektörünü veritabanına kaydeder.
        Aynı dosyaya ait eski chunk'lar önce silinir (ghost chunk engeli).
        Vektörler L2 normalize edilerek kaydedilir.
        """
        # Dosya başına grupla ve eski kayıtları temizle
        source_files = set(src for src, _, _, _ in records)
        rows = []
        for src, idx, txt, emb in records:
            vec = np.array(emb, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            rows.append((src, idx, txt, vec.tobytes()))

        with self._connect() as conn:
            for sf in source_files:
                conn.execute("DELETE FROM documents WHERE source_file = ?", (sf,))
            conn.executemany("""
                INSERT INTO documents (source_file, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?)
            """, rows)
            conn.commit()
        return len(rows)

    def search(self, query_embedding: List[float], top_k: int = TOP_K) -> List[SearchResult]:
        """Sorgu vektörü ile matris çarpımı yaparak kosinüs benzerliğine göre en yakın öbekleri getirir."""
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
            embeddings.append(vec)  # Vektörler kaydedilirken normalize edildi
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
        added_indices = set()
        file_counts = {}

        # 1. Pas: Kaynak çeşitliliğini korumak için dosya başına sınır uygula
        for sim, i in scored:
            if len(results) >= top_k:
                break
            src = sources[i]
            if file_counts.get(src, 0) < MAX_CHUNKS_PER_FILE:
                results.append(SearchResult(contents[i], sources[i], indices[i], float(sim)))
                file_counts[src] = file_counts.get(src, 0) + 1
                added_indices.add(i)

        # 2. Pas: Eşik dolmadıysa kalan en yüksek benzerlikleri ekle
        if len(results) < top_k:
            for sim, i in scored:
                if len(results) >= top_k:
                    break
                if i not in added_indices:
                    results.append(SearchResult(contents[i], sources[i], indices[i], float(sim)))
                    added_indices.add(i)

        return results

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
        """Veritabanındaki tüm verileri temizler."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM documents")
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
