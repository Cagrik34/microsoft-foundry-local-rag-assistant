"""
Model Yönetimi ve Veri Yapıları (src/core/models.py)
===================================================
Metin öbekleri, arama sonuçları ve Foundry Local SDK model sürücüsü.
"""

import sys
import concurrent.futures
from dataclasses import dataclass, field
from typing import List
from src.config import EMBEDDING_MODEL, CHAT_MODEL, APP_NAME, MAX_TOKENS


@dataclass
class TextChunk:
    """Metin öbeğini ve dosya kaynağını temsil eder."""
    content: str
    source_file: str
    chunk_index: int


@dataclass
class DocumentInfo:
    """Belge verilerini ve öbek listesini tutar."""
    file_path: str
    file_name: str
    content: str
    chunks: List[TextChunk] = field(default_factory=list)


@dataclass
class SearchResult:
    """Vektör arama sonucunu temsil eder."""
    content: str
    source_file: str
    chunk_index: int
    similarity: float


@dataclass
class RAGResponse:
    """RAG sorgu yanıtı ve kullanılan kaynakları temsil eder."""
    answer: str
    sources: List[SearchResult]
    context_used: str


class ModelManager:
    """Microsoft Foundry Local SDK ile yerel yapay zeka modellerini yönetir."""

    def __init__(self):
        self._manager = None
        self._embedding_model = None
        self._chat_model = None
        self._embedding_client = None
        self._chat_client = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def initialize(self) -> None:
        """Foundry Local SDK'yı yapılandırır ve başlatır."""
        from foundry_local_sdk import Configuration, FoundryLocalManager
        print("⚙️  Foundry Local SDK başlatılıyor...")
        config = Configuration(app_name=APP_NAME)
        FoundryLocalManager.initialize(config)
        self._manager = FoundryLocalManager.instance
        print("✅ SDK hazır.\n")

    def load_embedding_model(self) -> None:
        """Embedding modelini indirir ve belleğe yükler."""
        if self._embedding_client:
            return
        print(f"📦 Embedding modeli yükleniyor: {EMBEDDING_MODEL}")
        self._embedding_model = self._manager.catalog.get_model(EMBEDDING_MODEL)
        self._embedding_model.download(lambda p: print(f"\r   İndiriliyor: {p:.1f}%", end="", flush=True))
        print()
        self._embedding_model.load()
        self._embedding_client = self._embedding_model.get_embedding_client()
        print(f"✅ Embedding modeli hazır: {EMBEDDING_MODEL}\n")

    def load_chat_model(self) -> None:
        """Chat dil modelini indirir ve belleğe yükler."""
        if self._chat_client:
            return
        print(f"📦 Chat modeli yükleniyor: {CHAT_MODEL}")
        self._chat_model = self._manager.catalog.get_model(CHAT_MODEL)
        self._chat_model.download(lambda p: print(f"\r   İndiriliyor: {p:.1f}%", end="", flush=True))
        print()
        self._chat_model.load()
        self._chat_client = self._chat_model.get_chat_client()
        self._chat_client.settings.max_tokens = MAX_TOKENS
        self._chat_client.settings.temperature = 0.3
        self._chat_client.settings.presence_penalty = 0.1
        print(f"✅ Chat modeli hazır: {CHAT_MODEL}\n")

    def _ensure_executor(self) -> None:
        """ThreadPoolExecutor'ın aktif olduğunu doğrular, gerekirse yeniden oluşturur."""
        if self._executor is None or getattr(self._executor, "_shutdown", False):
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def generate_embedding(self, text: str) -> List[float]:
        """Metin için vektör üretir (Thread Pool İzoleli)."""
        if not self._embedding_client:
            raise RuntimeError("Embedding modeli yüklenmedi.")
        self._ensure_executor()
        try:
            future = self._executor.submit(self._embedding_client.generate_embedding, text)
            res = future.result(timeout=60)
            return res.data[0].embedding
        except Exception:
            return self._embedding_client.generate_embedding(text).data[0].embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Toplu metin listesi için vektörler üretir (Thread Pool İzoleli)."""
        if not self._embedding_client:
            raise RuntimeError("Embedding modeli yüklenmedi.")
        self._ensure_executor()
        try:
            future = self._executor.submit(self._embedding_client.generate_embeddings, texts)
            res = future.result(timeout=120)
            return [item.embedding for item in res.data]
        except Exception:
            return [item.embedding for item in self._embedding_client.generate_embeddings(texts).data]

    def chat_complete(self, messages: List[dict]) -> str:
        """Dil modeline istem gönderir ve yanıt üretir (Stateless & Thread Pool İzoleli).
        İlk deneme başarısız olursa taze gRPC istemcisi oluşturarak tekrar dener.
        """
        if not self._chat_model:
            raise RuntimeError("Chat modeli yüklenmedi.")
        self._ensure_executor()
        try:
            client = self._chat_client or self._chat_model.get_chat_client()
            client.settings.max_tokens = MAX_TOKENS
            client.settings.temperature = 0.3
            client.settings.presence_penalty = 0.1

            future = self._executor.submit(client.complete_chat, messages)
            res = future.result(timeout=120)
            return res.choices[0].message.content
        except Exception as e:
            # İlk deneme başarısız: bozuk gRPC kanalını atıp taze istemci oluştur
            try:
                print(f"\n⚠️  İlk chat denemesi başarısız ({type(e).__name__}), taze istemci ile yeniden deneniyor...", file=sys.stderr)
                fresh_client = self._chat_model.get_chat_client()
                fresh_client.settings.max_tokens = MAX_TOKENS
                fresh_client.settings.temperature = 0.3
                fresh_client.settings.presence_penalty = 0.1
                self._chat_client = fresh_client  # Taze istemciyi kalıcı yap

                self._ensure_executor()
                future = self._executor.submit(fresh_client.complete_chat, messages)
                res = future.result(timeout=120)
                return res.choices[0].message.content
            except Exception as e2:
                print(f"\n⚠️  Chat completion hatası: {e2}", file=sys.stderr)
                return f"Yanıt üretilemedi: {e2}"

    def shutdown(self) -> None:
        """Yüklü modelleri bellekten serbest bırakır."""
        try:
            if self._embedding_model:
                try:
                    self._embedding_model.unload()
                except Exception:
                    pass
                self._embedding_client = None
            if self._chat_model:
                try:
                    self._chat_model.unload()
                except Exception:
                    pass
                self._chat_client = None
            if self._executor:
                self._executor.shutdown(wait=False)
                self._executor = None
            print("🔌 Modeller bellekten kaldırıldı.")
        except Exception as e:
            print(f"⚠️  Kapatma hatası: {e}", file=sys.stderr)

    @property
    def is_embedding_ready(self) -> bool:
        return self._embedding_client is not None

    @property
    def is_chat_ready(self) -> bool:
        return self._chat_client is not None
