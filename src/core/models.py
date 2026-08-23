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
    """Hibrit arama sonucunu temsil eder."""
    content: str
    source_file: str
    chunk_index: int
    similarity: float
    citation_index: int = 1
    match_type: str = "hybrid"  # "vector", "bm25", "hybrid"

    @property
    def relevance_percentage(self) -> int:
        """Ham kosinüs/RRF skorunu sezgisel %50 - %99 anlamsal alaka düzeyine kalibre eder."""
        if self.similarity <= 0.0:
            return 0
        if self.similarity >= 0.9:
            return 100
        score = 50 + ((self.similarity - 0.05) / 0.35) * 48
        return max(10, min(99, int(round(score))))


@dataclass
class ChatMessage:
    """Kayıtlı sohbet mesajını temsil eder."""
    id: int
    session_id: str
    role: str
    content: str
    sources_json: str = ""
    search_time: float = 0.0
    gen_time: float = 0.0
    created_at: str = ""


@dataclass
class ChatSession:
    """Kayıtlı sohbet oturumunu temsil eder."""
    session_id: str
    title: str
    created_at: str = ""
    updated_at: str = ""


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
        """Foundry Local çalışma zamanını başlatır."""
        from foundry_local_sdk import Configuration, FoundryLocalManager
        try:
            if FoundryLocalManager.instance is not None:
                self._manager = FoundryLocalManager.instance
                return
        except Exception:
            pass

        print("⚙️  Foundry Local SDK başlatılıyor...")
        try:
            config = Configuration(app_name=APP_NAME)
            FoundryLocalManager.initialize(config)
            self._manager = FoundryLocalManager.instance
        except Exception:
            self._manager = FoundryLocalManager.instance
        print("✅ SDK hazır.\n")

    def load_embedding_model(self) -> None:
        """Embedding modelini indirir ve belleğe yükler."""
        if self._embedding_client:
            return
        if not self._manager:
            self.initialize()
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
        if not self._manager:
            self.initialize()
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
        """Metin için 1024 boyutlu yoğun vektör üretir."""
        if not self._embedding_client:
            self.load_embedding_model()
        try:
            return self._embedding_client.generate_embedding(text).data[0].embedding
        except Exception:
            # Gerekirse istemciyi yenileyip tekrar dene
            fresh = self._embedding_model.get_embedding_client()
            self._embedding_client = fresh
            return fresh.generate_embedding(text).data[0].embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Toplu metin listesi için vektörler üretir."""
        if not self._embedding_client:
            self.load_embedding_model()
        try:
            return [item.embedding for item in self._embedding_client.generate_embeddings(texts).data]
        except Exception:
            fresh = self._embedding_model.get_embedding_client()
            self._embedding_client = fresh
            return [item.embedding for item in fresh.generate_embeddings(texts).data]

    def chat_complete(self, messages: List[dict]) -> str:
        """Dil modeline istem gönderir ve doğrudan yanıt üretir.
        Gerekirse taze istemci ile otomatik kurtarma yapar.
        """
        if not self._chat_model:
            self.load_chat_model()
        try:
            client = self._chat_client or self._chat_model.get_chat_client()
            client.settings.max_tokens = MAX_TOKENS
            client.settings.temperature = 0.3
            client.settings.presence_penalty = 0.1
            res = client.complete_chat(messages)
            return res.choices[0].message.content
        except Exception as e:
            try:
                print(f"\n⚠️  Chat tamamlanamadı ({e}), taze istemci ile deneniyor...", file=sys.stderr)
                fresh_client = self._chat_model.get_chat_client()
                fresh_client.settings.max_tokens = MAX_TOKENS
                fresh_client.settings.temperature = 0.3
                fresh_client.settings.presence_penalty = 0.1
                self._chat_client = fresh_client
                res = fresh_client.complete_chat(messages)
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
