"""
Konfigürasyon Modülü (src/config.py)
===================================
Tüm proje ayarlarını ve model tanımlarını saklar.
"""

import os

# Proje kök dizini (microsoft-foundry-local-rag-assistant/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Model Ayarları (Foundry Local Katalog İsimleri)
EMBEDDING_MODEL = "qwen3-embedding-0.6b"  # Türkçe ve çok dilli embedding modeli (~600 MB, 1024 boyut)
CHAT_MODEL = "phi-3.5-mini"               # Microsoft'un yüksek hızlı, kusursuz yerel Instruct dili modeli (~2.2 GB, 3.8B)
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
TOP_K = 3               # Aramada getirilecek en yüksek puanlı öbek sayısı (Kapsayıcı tam arama)
SIMILARITY_THRESHOLD = 0.05  # Minimum kosinüs benzerlik eşiği
MAX_CHUNKS_PER_FILE = 3      # Aynı dosyadan seçilebilecek maksimum öbek sayısı
MAX_CONTEXT_CHARS = 1600     # Bağlam penceresi ideal karakter sınırı (Eksiksiz bilgi + 12s CPU yanıtı)
MAX_TOKENS = 256             # LLM yanıt üretim limiti (token)

# Sistem Komutları (System Prompts)
SYSTEM_PROMPT = """You are a precise document assistant. Answer the question in clean, grammatically correct Turkish using ONLY the information in <DOCUMENTS> below.
If the answer is not in <DOCUMENTS>, respond with: "Bu bilgi belgelerde bulunmuyor."
Be direct and concise — output only the exact answer.

<DOCUMENTS>
{context}
</DOCUMENTS>"""

SYSTEM_PROMPT_EN = """You are a precise document assistant. Answer the question in English using ONLY the information in <DOCUMENTS> below.
If the answer is not in <DOCUMENTS>, respond with: "This information is not found in the documents."
Be direct and concise — output only the exact answer.

<DOCUMENTS>
{context}
</DOCUMENTS>"""

SYSTEM_PROMPT_SUMMARIZE = """You are a document summarizer. Summarize the text below in Turkish in maximum 4 concise sentences.

DOCUMENT CONTENT:
{context}"""

CONTEXT_CHUNK_TEMPLATE = "[Kaynak Dosya: {source} | Bölüm: {index}]\n{content}\n"
