"""
Konfigürasyon Modülü (src/config.py)
===================================
Tüm proje ayarlarını ve model tanımlarını saklar.
"""

import os

# Proje kök dizini (microsoft-foundry-local-rag-assistant/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Model Ayarları (Foundry Local Katalog İsimleri) ──
# Embedding: qwen3-embedding-0.6b — Türkçe ve çok dilli, 1024 boyut, CPU'da hızlı (~600 MB)
EMBEDDING_MODEL = "qwen3-embedding-0.6b"

# Chat: Varsayılan phi-3.5-mini — 3.8B, CPU'da hızlı (8-10 tok/s), kanıtlanmış kararlılık
# Alternatif: "qwen3-4b" — 4B, reasoning destekli, daha iyi Türkçe, benzer CPU hızı
CHAT_MODEL = "phi-3.5-mini"

APP_NAME = "rag_assistant"

# Belge ve Veritabanı Dizinleri
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx", ".xlsx", ".pptx"}
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "rag_knowledge.db")

# Öbekleme (Chunking) ve Arama Ayarları
CHUNK_SIZE = 1000       # Bir metin öbeğinin maksimum karakter uzunluğu
CHUNK_OVERLAP = 200     # Öbekler arası örtüşme miktarı
MIN_CHUNK_LENGTH = 50   # Minimum geçerli öbek uzunluğu
TOP_K = 3               # Aramada getirilecek en yüksek puanlı öbek sayısı
SIMILARITY_THRESHOLD = 0.05  # Minimum kosinüs benzerlik eşiği
MAX_CHUNKS_PER_FILE = 3      # Aynı dosyadan seçilebilecek maksimum öbek sayısı
MAX_CONTEXT_CHARS = 1000     # Bağlam penceresi karakter sınırı (CPU hız/kapsam dengesi)
MAX_TOKENS = 150             # LLM yanıt üretim limiti (token)

# ── Sistem Komutları (System Prompts) ──
SYSTEM_PROMPT = """You are a precise document assistant. Answer ONLY in Turkish.
RULES:
1. Use ONLY the information in <DOCUMENTS> below.
2. Be direct — answer in maximum 2-3 sentences. No filler phrases like "Belgelere göre..." or greetings.
3. If the answer is not in <DOCUMENTS>, respond with: "Bu bilgi belgelerde bulunmuyor."

<DOCUMENTS>
{context}
</DOCUMENTS>"""

SYSTEM_PROMPT_EN = """You are a precise document assistant. Answer ONLY in English.
RULES:
1. Use ONLY the information in <DOCUMENTS> below.
2. Be direct — answer in maximum 2-3 sentences. No filler phrases or greetings.
3. If the answer is not in <DOCUMENTS>, respond with: "This information is not found in the documents."

<DOCUMENTS>
{context}
</DOCUMENTS>"""

SYSTEM_PROMPT_SUMMARIZE = """Summarize the text below in Turkish in maximum 3 concise sentences. Be direct, no filler phrases.

DOCUMENT CONTENT:
{context}"""

CONTEXT_CHUNK_TEMPLATE = "[Kaynak Dosya: {source} | Bölüm: {index}]\n{content}\n"

