"""
Konfigürasyon Modülü (src/config.py)
===================================
Tüm proje ayarlarını, model tanımlarını, hibrit arama parametrelerini ve sistem komutlarını saklar.
"""

import os

# Proje kök dizini (microsoft-foundry-local-rag-assistant/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Model Ayarları (Foundry Local Katalog İsimleri) ──
# Embedding: qwen3-embedding-0.6b — Türkçe ve çok dilli, 1024 boyut, CPU'da hızlı (~600 MB)
EMBEDDING_MODEL = "qwen3-embedding-0.6b"

# Chat: phi-4-mini — Microsoft 3.8B SOTA Model, CPU'da ultra hızlı, gelişmiş Türkçe akıl yürütme
CHAT_MODEL = "phi-4-mini"

APP_NAME = "rag_assistant"

# Belge ve Veritabanı Dizinleri
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".xlsx", ".pptx"}
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "rag_knowledge.db")

# Öbekleme (Chunking) ve Arama Ayarları
CHUNK_SIZE = 1000            # Bir metin öbeğinin maksimum karakter uzunluğu
CHUNK_OVERLAP = 200          # Öbekler arası örtüşme miktarı
MIN_CHUNK_LENGTH = 50        # Minimum geçerli öbek uzunluğu
TOP_K = 3                    # Aramada getirilecek en yüksek puanlı öbek sayısı
SIMILARITY_THRESHOLD = 0.20  # Minimum kosinüs benzerlik eşiği
MAX_CHUNKS_PER_FILE = 1      # Her dosyadan en yüksek puanlı 1 öbek seç (bağlam çeşitliliği)
MAX_CONTEXT_CHARS = 3000     # Bağlam penceresi karakter sınırı
MAX_TOKENS = 180             # LLM yanıt üretim limiti (token)

# ── Hibrit Arama (Dense Vector + BM25 FTS5 + RRF) Ayarları ──
HYBRID_ALPHA = 0.5           # Vektör ve BM25 ağırlık dengesi (0.0 = Sadece BM25, 1.0 = Sadece Vektör)
RRF_K = 60                   # Reciprocal Rank Fusion yumuşatma sabiti (Endüstri standardı)

# ── Sistem Komutları (System Prompts) ──
SYSTEM_PROMPT = """You are a precise document assistant. Answer ONLY in Turkish.
RULES:
1. Base your answer strictly on the provided <DOCUMENTS>.
2. Cite sources using [1], [2] at the end of sentences that reference them (e.g. "Bütçe 2.340.000 TL'dir [1].").
3. Answer directly and concisely in 2-4 sentences. Do not add conversational filler.
4. Only if the documents contain no relevant information at all, state: "Bu bilgi indeksli belgelerde yer almamaktadır."

<DOCUMENTS>
{context}
</DOCUMENTS>"""

SYSTEM_PROMPT_EN = """You are a precise document assistant. Answer ONLY in English.
RULES:
1. Base your answer strictly on the provided <DOCUMENTS>.
2. Cite sources using [1], [2] at the end of sentences that reference them (e.g. "The budget is 2.34M [1].").
3. Answer directly and concisely in 2-4 sentences. Do not add conversational filler.
4. Only if the documents contain no relevant information at all, state: "This information is not found in the indexed documents."

<DOCUMENTS>
{context}
</DOCUMENTS>"""

SYSTEM_PROMPT_SUMMARIZE = """Summarize the text below in Turkish in maximum 3 concise sentences. Be direct, no filler phrases.

DOCUMENT CONTENT:
{context}"""

CONTEXT_CHUNK_TEMPLATE = "[Kaynak {num}: {source} | Bölüm {index}]\n{content}\n"
