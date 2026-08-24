# ⚡ Zenith AI — Gizlilik Odaklı Yerel RAG Asistanı

**Microsoft Foundry Local SDK, Hibrit Arama (Dense + SQLite FTS5 BM25 + RRF), Metin İçi Alıntılar, Çift Yönlü Sesli Yapay Zeka, Temiz React Custom Hooks ve FastAPI Mimarisi.**

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Frontend: React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20Tailwind-cyan.svg)](https://react.dev/)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI%20SSE%20Stream-emerald.svg)](https://fastapi.tiangolo.com/)
[![Docker: Supported](https://img.shields.io/badge/Docker-Multi--stage%20Build-blue.svg)](Dockerfile)
[![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-Automated%20Testing-green.svg)](.github/workflows/ci.yml)

[🌐 English Documentation](README.md)

---

## 📌 Genel Bakış

**Zenith AI**, hassas kurumsal belgelerin harici bulut sunucularına iletilmeden, %100 yerel donanımda analiz edilmesi amacıyla tasarlanmış bir Yerel RAG (Retrieval-Augmented Generation) asistanıdır.

**Microsoft Foundry Local SDK** ile güçlendirilen sistem; yerel Küçük Dil Modellerini (**`phi-4-mini`** 3.8B Instruct) ve Yoğun Vektör Modellerini (**`qwen3-embedding-0.6b`** 1024 boyutlu) doğrudan yerel CPU üzerinde çalıştırır. Sıfır bulut bağımlılığı ve sıfır API maliyetiyle tüm belgeler, gömmeler ve sohbet geçmişleri yalnızca cihazınızda saklanır.

---

## 🏛️ Sistem Mimarisi

```text
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                   FRONTEND: React 18 + Vite + TypeScript + Tailwind CSS                    │
│   (Custom Hooks: useSessions, useChatStream, useDocumentIngest, useDbStats, 60fps Audio)   │
└────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ HTTP / Server-Sent Events (SSE)
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 BACKEND: FastAPI + Uvicorn                                 │
│          (Asenkron REST API, Çoklu Oturum Yönetimi, Yapılandırılmış Loglama)               │
└────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                          RAG MOTORU: Hibrit Arama & SQLite FTS5                            │
│              (Dense Vektörler + SQLite FTS5 BM25 + Reciprocal Rank Fusion RRF)             │
└──────────────────────────┬───────────────────────────────────────────┬─────────────────────┘
                           │ (Vektör & Metin Erişimi)                  │ (Yerel Model Çıkarımı)
                           ▼                                           ▼
       ┌───────────────────────────────────────┐      ┌────────────────────────────────────────┐
       │    SQLite Yerel Depo & FTS5 İndeksi   │      │      Microsoft Foundry Local SDK       │
       │  - documents (1024-d L2 Vektörleri)   │      │  - qwen3-embedding-0.6b (1024-d)       │
       │  - documents_fts (unicode61 BM25)     │      │  - phi-4-mini (3.8B Instruct)          │
       │  - chat_sessions & chat_messages      │      └────────────────────────────────────────┘
       └───────────────────────────────────────┘
```

---

## 🌟 Öne Çıkan Mühendislik Nitelikleri

### 1. 🔍 Hibrit Arama Motoru (Dense + BM25 + RRF)
- **Dense Vektör Arama:** `qwen3-embedding-0.6b` ile 1024 boyutlu anlamsal benzerlik.
- **Kelime Bazlı BM25 Arama:** Tam anahtar kelime, kısaltma ve teknik terim eşleşmeleri için `unicode61` tokenizer'lı SQLite `FTS5` sanal tablosu.
- **Reciprocal Rank Fusion (RRF):** Vektör ve kelime sıralamalarını dengeli bir skorda birleştirir:
  $$RRF(d) = \frac{\alpha}{k + rank_{dense}(d)} + \frac{1 - \alpha}{k + rank_{bm25}(d)} \quad (k=60, \alpha=0.5)$$

### 2. 🎯 Metin İçi Kaynak Alıntıları `[1]`, `[2]`
- Üretilen yanıta doğrudan gömülen Perplexity tarzı etkileşimli kaynak rozetleri.
- Rozetin üzerine gelindiğinde dosya adı, bölüm numarası, benzerlik yüzdesi ve kaynak metin parçacığını gösteren araç ipucu.

### 3. 📊 Yapı Duyarlı Belge Ayrıştırma ve Tablo Koruma
- **Excel (`.xlsx`):** Tablo satırlarını başlık bütünlüğünü koruyarak Markdown Pipe Tablolarına (`| Sütun | Değer |`) dönüştürür.
- **Word (`.docx`) & PDF:** Başlık hiyerarşisi (`#`, `##`, `###`) ve sayfa numaraları korunur.
- **Desteklenen Formatlar:** `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.txt`.

### 4. 🎙️ Çift Yönlü Sesli Yapay Zeka (Whisper STT & TTS)
- **Canlı Ses Dalgası:** Ses perdesi ve desibele anlık tepki veren 60 FPS frekans görselleştirici (`Web Audio API`).
- **Çevrimdışı Whisper STT:** `faster-whisper` (CTranslate2 INT8) ile %100 yerel Türkçe ses tanıma.

### 5. 🧩 Modüler Frontend Mimarisi (Custom Hooks)
- **`useSessions`:** SQLite çoklu oturum geçmişi, geçiş ve silme işlemleri.
- **`useChatStream`:** SSE token akışı, metin içi alıntı ayrıştırma ve hata yönetimi.
- **`useDocumentIngest`:** Dosya yükleme, dizin tarama ve veritabanı sıfırlama işlemleri.
- **`useDbStats`:** Veritabanı boyutu ve öbek sayısı telemetrisi.

---

## 📊 RAG Kalite & Benchmark Metrikleri

Depo içerisinde yerleşik RAG kalite ölçüm süiti (`src/core/evaluator.py` ve `tests/test_evaluation_benchmark.py`) bulunmaktadır:

| Değerlendirme Metriği | Skor | Hedef Eşik | Açıklama |
|---|---|---|---|
| **Toplam Kalite Skoru (Composite)** | **%89.4** | > %75 | Ağırlıklı genel RAG performans skoru |
| **Faithfulness (Sadakat)** | **%96.2** | > %85 | Bağlama sadakat / Halüsinasyon içermeme |
| **Groundedness (Alıntı Geçerliliği)** | **%100.0** | > %80 | `[1]`, `[2]` alıntılarının kaynaklarla tam tutarlılığı |
| **Keyword Recall (Anahtar Terim Kapsama)** | **%100.0** | > %75 | Hedef alandaki kritik terimlerin yanıtta yer alma oranı |
| **Arama Gecikmesi (Search Latency)** | **0.65s** | < 1.5s | Hibrit Dense + FTS5 arama tamamlama süresi |

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.11+
- Node.js 18+ (React frontend derlemesi için)
- Microsoft Foundry Local SDK

### Yöntem A: Yerel Çalıştırma
```powershell
# 1. Repoyu klonlayın
git clone https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant.git
cd microsoft-foundry-local-rag-assistant

# 2. Python bağımlılıklarını kurun
pip install -r requirements.txt

# 3. Frontend paketini derleyin (değişiklik yapıldıysa)
cd frontend
npm install
npm run build
cd ..

# 4. Uygulamayı başlatın
python app.py
```

### Yöntem B: Docker Konteyneri
```powershell
# Docker Compose ile tek komutla başlatma
docker compose up --build -d
```
Arayüze `http://localhost:8000` adresinden erişebilirsiniz.

---

## 🧪 Testler ve Doğrulama

```powershell
# 1. 360° Entegrasyon Test Süiti
python tests/test_360_suite.py

# 2. RAG Kalite Benchmark Testi
python tests/test_evaluation_benchmark.py

# 3. Frontend Tip ve Derleme Kontrolü
cd frontend && npm run build
```

---

## 📜 Lisans

**MIT Lisansı** ile dağıtılmaktadır. Detaylar için [`LICENSE`](LICENSE) dosyasına bakınız.

**Geliştirici:** Çağrı Giray Keşan  
**Telif Hakkı:** © 2026 Çağrı Giray Keşan. Tüm Hakları Saklıdır.
