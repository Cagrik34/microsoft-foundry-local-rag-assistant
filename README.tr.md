# ⚡ Zenith AI — Kurumsal SOTA Yerel & Gizli RAG Asistanı

**Yüksek Performanslı Çevrimdışı Doküman Zekası, Hibrit Arama (Dense + FTS5 BM25 + RRF), Cümle İçi Alıntılar, Çift Yönlü Sesli Asistan ve Modern React + FastAPI Mimarisi.**

[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Ön Yüz: React 18](https://img.shields.io/badge/%C3%96n%20Y%C3%BCz-React%2018%20%2B%20Vite%20%2B%20Tailwind-cyan.svg)](https://react.dev/)
[![Arka Yüz: FastAPI](https://img.shields.io/badge/Arka%20Y%C3%BCz-FastAPI%20SSE%20Canl%C4%B1%20Ak%C4%B1%C5%9F-emerald.svg)](https://fastapi.tiangolo.com/)
[![Platform: Yerel AI](https://img.shields.io/badge/Platform-Microsoft%20Foundry%20Local-indigo.svg)](https://azure.microsoft.com/)
[![Gizlilik: Sıfır Sızıntı](https://img.shields.io/badge/Gizlilik-%25100%20%C3%87evrimd%C4%B1%C5%9F%C4%B1%20S%C4%B1f%C4%B1r%20Veri%20S%C4%B1z%C4%B1nt%C4%B1s%C4%B1-emerald.svg)](#-g%C3%BCvenlik-ve-s%C4%B1f%C4%B1r-veri-s%C4%B1z%C4%B1nt%C4%B1s%C4%B1-mimarisi)

---

## 📌 Genel Bakış

**Zenith AI**, Microsoft Foundry Local SDK altyapısını kullanan, kurumsal düzeyde yüksek performanslı ve %100 çevrimdışı bir Doküman Analiz ve Soru-Cevap (RAG) asistanıdır.

**Microsoft Foundry Local SDK** altyapısıyla çalışan sistem, yerel Büyük Dil Modellerini (**`phi-4-mini`** 3.8B) ve Vektör Modellerini (**`qwen3-embedding-0.6b`** 1024 boyutlu) doğrudan bilgisayarınızın kendi donanımında (CPU) çalıştırır. Sıfır bulut bağımlılığı, sıfır API maliyeti ve sıfır veri sızıntısı ile tüm gizli şirket dokümanlarınız ve analizleriniz cihazınızda kalır.

---

## 🏛️ Sistem Mimarisi

```text
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                    ÖN YÜZ: React 18 + Vite + TypeScript + Tailwind CSS                     │
│    (ChatGPT/Perplexity Standardı Koyu UI, Canlı SSE Akış, STT Mikrofon, TTS, Alıntılar)    │
└────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │ HTTP / Server-Sent Events (SSE)
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                ARKA YÜZ: FastAPI + Uvicorn                                 │
│                (Asenkron REST API, Çoklu Oturum Yönetimi, Sıfır Kilitlenme)                │
└────────────────────────────────────────────┬───────────────────────────────────────────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                           RAG MOTORU: Hibrit Arama & SQLite FTS5                           │
│             (Yoğun Vektörler + SQLite FTS5 BM25 + Reciprocal Rank Fusion RRF)              │
└──────────────────────────┬───────────────────────────────────────────┬─────────────────────┘
                           │ (Vektör & Metin Arama)                    │ (Yerel Çıkarım)
                           ▼                                           ▼
       ┌───────────────────────────────────────┐      ┌────────────────────────────────────────┐
       │    SQLite Yerel Depo & FTS5 İndeksi   │      │      Microsoft Foundry Local SDK       │
       │  - documents (1024-d L2 Vektörler)    │      │  - qwen3-embedding-0.6b (1024-d)       │
       │  - documents_fts (unicode61 BM25)     │      │  - phi-4-mini (3.8B Instruct)          │
       │  - chat_sessions & chat_messages      │      └────────────────────────────────────────┘
       └───────────────────────────────────────┘
```

---

## 🌟 Temel Yetenekler ve Mühendislik Özellikleri

### 1. 🔍 Hibrit Arama Motoru (Dense + BM25 + RRF)
* **Yoğun Vektör Araması:** `qwen3-embedding-0.6b` ile 1024 boyutlu anlamsal kosinüs benzerliği.
* **Tam Metin (BM25) Araması:** SQLite `FTS5` (`unicode61` tokenizer) ile ürün kodları, kısaltmalar ve tam terim eşleşmesi.
* **Reciprocal Rank Fusion (RRF):** Her iki arama sonucunu tek bir optimize alaka puanında birleştirir:
  $$RRF(d) = \frac{\alpha}{k + rank_{dense}(d)} + \frac{1 - \alpha}{k + rank_{bm25}(d)}$$

### 2. 🎯 Cümle İçi İnteraktif Alıntılar `[1]`, `[2]` (Perplexity Tarzı)
* Yanıt içindeki her iddianın sonuna yerleştirilen interaktif rozetler.
* Rozetin üzerine gelindiğinde kaynak dosya adı, bölüm numarası, alaka yüzdesi ve ilgili metin parçası hover kartı olarak açılır.

### 3. 📊 Yapı Duyarlı Tablo Ayrıştırma
* **Excel (`.xlsx`):** Sayfa verilerini satır/sütun ilişkisini koruyarak Markdown Pipe Tablosu (`| Sütun | Değer |`) formatında saklar.
* **Word (`.docx`) & PDF:** Başlık hiyerarşisi (`# Başlık 1`, `## Başlık 2`) ve tablo hücreleri korunur.
* **Formatlar:** `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.txt`.

### 4. 🎙️ Çift Yönlü Sesli Asistan (Web Speech STT/TTS)
* **Sesli Soru Sorma (STT):** Tarayıcı yerel ses tanıma API'si ile Türkçe canlı konuşma tanıma.
* **Seslendirme (TTS):** Üretilen yanıtı tek tıkla doğal Türkçe sesle dinleme.

### 5. 📁 Çoklu Sohbet Oturumu ve Kalıcı Hafıza
* Sol menüden yeni sohbet oturumları açabilme ve geçmiş analizler arasında geçiş yapma.
* SQLite `chat_sessions` ve `chat_messages` tabloları ile kalıcı saklama.
* Sohbet geçmişini tek tıkla Markdown (`.md`) formatında indirme.

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
* Python 3.11+
* Node.js 18+ (Frontend derlemesi için)
* Microsoft Foundry Local SDK

### 1. Projeyi Klonlayın ve Bağımlılıkları Yükleyin
```powershell
git clone https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant.git
cd microsoft-foundry-local-rag-assistant

# Python bağımlılıklarını yükleyin
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatın
```powershell
python app.py
```

* **Seçenek `[1]`:** Terminal (CLI) Modu (ANSI renkli konsol).
* **Seçenek `[2]`:** Web Uygulaması (FastAPI sunucusunu başlatır ve `http://localhost:8000` adresini tarayıcıda otomatik açar).

---

## ⚙️ Teknik Parametreler

| Bileşen | Değer | Açıklama |
|---|---|---|
| **Çıkarım Modeli** | `phi-4-mini` (3.8B) | Microsoft Foundry Local CPU çıkarımı (~15-20s yanıt süresi) |
| **Vektör Modeli** | `qwen3-embedding-0.6b` | 1024 boyutlu yoğun vektör (~600 MB RAM) |
| **Veritabanı** | SQLite + FTS5 | Sunucusuz, sıfır yapılandırma, tek dosya (`data/rag_knowledge.db`) |
| **Arama Motoru** | Hibrit (Dense + BM25) | Reciprocal Rank Fusion ($k=60, \alpha=0.5$) |
| **Ön Yüz** | React 18 + Vite + Tailwind | Koyu Silicon Valley teması, SSE canlı akış |
| **Arka Yüz** | FastAPI + Uvicorn | Asenkron REST + SSE |
| **Maliyet** | **0 TL / 0 USD** | %100 Ücretsiz, Açık Kaynaklı, Sıfır Bulut Bağımlılığı |

---

## 📄 Lisans
MIT Lisansı. Kurumsal doküman analizi ve açık kaynaklı yerel yapay zeka sistemleri için geliştirilmiştir.
