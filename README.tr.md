# ⚡ Zenith AI — Yerel ve Gizli Kurumsal RAG Asistanı

**Yüksek Performanslı Çevrimdışı Doküman Analizi, Sıfır Veri Sızıntısı RAG Mimarisi & Web Speech Ses Motoru.**

[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-purple.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Platform: Yerel AI](https://img.shields.io/badge/Platform-Microsoft%20Foundry%20Local-indigo.svg)](https://azure.microsoft.com/)
[![Gizlilik: Sıfır Sızıntı](https://img.shields.io/badge/Gizlilik-%25100%20%C3%87evrimd%C4%B1%C5%9F%C4%B1%20S%C4%B1f%C4%B1r%20S%C4%B1z%C4%B1nt%C4%B1-emerald.svg)](#-güvenlik-ve-sıfır-veri-sızıntısı-mimarisi)
[![Erişilebilirlik: WCAG 2.1](https://img.shields.io/badge/Eri%C5%9Filebilirlik-Web%20Speech%20TTS-pink.svg)](#-temel-modüller-ve-yetenekler)

[🇬🇧 Click here for English Documentation](https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant/blob/main/README.md)

---

## 📌 Genel Bakış

**Zenith AI**, kurumsal doküman analitiği, gizli finansal/hukuki rapor incelemeleri ve sıfır veri sızıntısı güvenliği için tasarlanmış açık kaynaklı, kurumsal standartta yerel bir Retrieval-Augmented Generation (RAG) asistanıdır.

**Microsoft Foundry Local SDK** altyapısı üzerinde çalışan Zenith AI, yerel büyük dil modelini (**`phi-3.5-mini`** 3.8B Instruct) ve vektör embedding modelini (**`qwen3-embedding-0.6b`** 1024-boyut) doğrudan yerel CPU/donanımınızda yürütür. **Sıfır Veri Sızıntısı Mimarisi** sayesinde hiçbir doküman, vektör, soru veya telemetri verisi cihazınızdan dışarı çıkmaz.

---

## 🏛️ Sistem Mimarisi ve Veri Akış Şeması

```text
                               ┌────────────────────────────────────────┐
                               │      Kullanıcı Arayüzü (UI Katmanı)     │
                               │  [Web (Streamlit)]  |  [Terminal CLI]  │
                               └───────────────────┬────────────────────┘
                                                   │ (Olay Dağıtımı)
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │        RAG Orkestrasyon Motoru         │
                               │          (src/core/engine.py)          │
                               └─────────┬────────────────────┬─────────┘
                                         │                    │
                    (Vektör Arama)       │                    │ (Metin Üretimi)
                                         ▼                    ▼
             ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
             │ SQLite Vektör Deposu (database.py)│    │ Model Yöneticisi (src/core/models)│
             │   - L2 Normalize Kosinüs Motoru   │    │   - Kalıcı ThreadPool İzolasyonu   │
             │   - Hayalet Chunk Koruma Sistemi  │    │   - Durumsuz ChatClient Üretimi  │
             └───────────────────────────────────┘    └─────────────────┬─────────────────┘
                                                                        │ (Native C++ gRPC)
                                                                        ▼
                                                      ┌───────────────────────────────────┐
                                                      │    Microsoft Foundry Local SDK    │
                                                      │  - qwen3-embedding-0.6b (1024-d)  │
                                                      │  - phi-3.5-mini (3.8B Instruct)   │
                                                      └───────────────────────────────────┘
```

---

## 🌟 Temel Modüller ve Yetenekler

### 1. 🌐 Çift Modlu Çalışma Mimarisi (Dual-Mode)
- **Gemini Live Stili Web Paneli (`src/ui/web.py`):** Dalgalı hareketli gradyanlar, aura ışık küreleri, cam efektli (glassmorphism) yan panel, mükerrer yazmayı engelleyen sürükle-bırak dosya yükleyici ve Markdown sohbet raporu dışa aktarımı.
- **Hafif Terminal CLI (`app.py` / `src/ui/cli.py`):** Windows UTF-8 akış korumalı (`cp1254` çökme dirençli), ANSI renklendirmeli ve anlık kelime akışlı konsol arayüzü.

### 2. 📑 Çoklu Format Belge İşleme Hattı (`src/core/document_loader.py`)
- Kapsamlı metin ve yapı ayıklama desteği:
  - **Markdown (`.md`) ve Düz Metin (`.txt`):** Çoklu kodlama algılama (`utf-8`, `utf-8-sig`, `cp1254`, `latin-1`).
  - **Adobe PDF (`.pdf`):** `pypdf` ile çok sayfalı metin çıkarma.
  - **Word (`.docx`):** `python-docx` ile paragraf ve tablo okuma.
  - **Excel (`.xlsx`):** `openpyxl` ile çok sayfalı hücre ve satır verisi okuma.
  - **PowerPoint (`.pptx`):** `python-pptx` ile slayt ve şekil metinleri çıkarma.
- **Hata Metni Koruma Sistemi:** Okunamayan belgeler veya eksik kütüphaneler veritabanına hata dizesi kaydetmez; sessizce atlanır.

### 3. 🗄️ SQLite Vektör Deposu & L2 Normalize Arama (`src/core/database.py`)
- Sunucu gerektirmeyen hafif SQLite vektör deposu (`data/rag_knowledge.db`).
- **L2 Ön-Normalizasyon:** Vektörler kaydedilirken normalize edilir; böylece arama anında kosinüs benzerliği tek bir matris çarpımına (`matrix @ q_vec`) dönüşür.
- **Hayalet Chunk (Ghost Chunks) Temizliği:** Yeniden indekslenen dosyaların eski fazla parçaları yazılmadan önce silinir.

### 4. ⚡ RAG Orkestrasyonu & Tek Çağrılı Özetleme (`src/core/engine.py`)
- **Tek Çağrılı Çoklu Dosya Özetleme (`_summarize_per_file`):** Dosya özetlerini tek bir birleşik LLM çağrısında toplayarak seri LLM bekleme süresini 75s+'den ~8s'ye indirir.
- **Akıllı Sorgu Yönlendirme (`_is_summary_query`):** Genel özet isteklerini spesifik sorulardan ("güvenlik açıklarını özetle") ayırt ederek RAG vektör aramasını korur.
- **Çift Dil Desteği:** Regex tabanlı İngilizce dil algılama ile doğru sistem istemini otomatik seçer.

### 5. 🧠 ThreadPool İzoleli Foundry Local Motoru (`src/core/models.py`)
- **Event Loop Kilitlenme Savunması:** C++ native gRPC çağrıları kalıcı `ThreadPoolExecutor(max_workers=1)` içinde çalıştırılarak Streamlit `asyncio` döngüsü kilitlenmeleri önlenir.
- **Durumsuz (Stateless) İstemci:** Her sorguda taze `ChatClient` üretilerek bellek sızıntısı ve bağlam şişmesi engellenir.

### 6. 🔊 Web Speech Erişilebilirlik ve Sesli Yapay Zeka (`Web Speech API`)
- Tarayıcının yerel Türkçe konuşma motoru üzerinden %100 çevrimdışı seslendirme.
- WCAG 2.1 standartlarına uygun tek tıkla ekran okuyucu ses desteği.

### 7. 🚪 Anlık İşletim Sistemi Kapanışı
- Modelleri RAM'den boşaltıp 0.3 saniye içinde `os._exit(0)` ile terminali anında serbest bırakan temiz çıkış mekanizması.

---

## ⚙️ Teknik Parametreler ve RAG Ayarları

| Parametre | Değer | Açıklama |
|---|---|---|
| **Embedding Modeli** | `qwen3-embedding-0.6b` | Türkçe ve çok dilli vektörleştirme (~600 MB RAM, 1024 boyut) |
| **Chat Modeli** | `phi-3.5-mini` (3.8B) | Microsoft 3.8B Instruct modeli; yüksek CPU hızı (8-10 tok/s), sıfır zaman aşımı |
| **Alternatif Chat Modeli** | `qwen3-4b` | `src/config.py` içinde belgelenmiş gelişmiş mantık yürütme modeli |
| **Öbek Uzunluğu (Chunk Size)** | `1000` karakter | Anlamsal bütünlük sağlayan bölümleme sınırı |
| **Öbek Örtüşmesi (Overlap)** | `200` karakter | Parçalar arası bağlam kopmasını önleyen kayan pencere |
| **Benzerlik Eşiği** | `0.05` | Gürültüyü filtreleyen minimum kosinüs benzerliği |
| **Arama Limiti (Top-K)** | `3` öbek | Yanıta dahil edilen en yüksek puanlı öbek sayısı |
| **Bağlam Limiti (Max Context)** | `1000` karakter | CPU ön-işleme (prefill) hızı için optimize bağlam penceresi (~280 token) |
| **Maksimum Token Sınırı** | `150` token | Gevezeliği önleyen, hızlı 2-3 cümlelik yanıt sınırı |

---

## 🛠️ Mühendislik Atılımları ve Gecikme Optimizasyonları

### 1. Streamlit AsyncIO & Native C++ gRPC Kilitlenme Çözümü
* **Sorun:** Microsoft Foundry SDK'nın native gRPC sürücüsü, ana iş parçacığındaki Streamlit `asyncio` döngüsüyle çakışarak 180s donmalara ve `Operation was cancelled` zaman aşımlarına yol açıyordu.
* **Çözüm:** Tüm embedding üretimi ve sohbet tamamlamaları kalıcı bir `ThreadPoolExecutor(max_workers=1)` izole iş parçacığına yönlendirildi.

### 2. Çoklu Dosya Özetleme Gecikmesinin Düşürülmesi ($O(N) \to O(1)$)
* **Sorun:** $N$ adet indeksli dosyanın özetlenmesi önceden $N$ adet sıralı senkron LLM çağrısı tetikliyordu ($N \times 25\text{s} = 75\text{s}+$).
* **Çözüm:** Birleşik bağlamsal istem yapısına dönüştürülerek tüm çoklu dosya yönetici özeti tek bir ~8s çıkarım çağrısında üretildi.

### 3. Hayalet Chunk'lar ve L2 Ön-Normalizasyonu
* **Sorun:** Kısaltılmış dosyaların yeniden indekslenmesi SQLite içinde eski öksüz parçalar bırakıyordu (`INSERT OR REPLACE` yalnızca eşleşen indeksleri güncelliyordu).
* **Çözüm:** Yazma öncesi temizlik (`DELETE FROM documents WHERE source_file = ?`) ve birim L2 vektör depolaması uygulandı.

### 4. Windows UTF-8 Terminal Çökme Koruması
* **Sorun:** Windows komut satırı kod sayfaları (`cp1254`/`cp1252`) durum emojilerini yazdırırken `UnicodeEncodeError` üretiyordu.
* **Çözüm:** Hem `app.py` hem de `src/ui/cli.py` içinde çalışma anı `sys.stdout` ve `sys.stderr` UTF-8 akış sarmalayıcıları entegre edildi.

---

## 🚀 Kurulum ve Başlatma

### Gereksinimler
- **İşletim Sistemi:** Windows 10/11, macOS veya Linux
- **Python:** Python 3.11 veya üstü
- **RAM:** Minimum 8 GB (16 GB önerilir)
- **Disk:** ~3 GB boş alan (modeller ilk çalıştırmada yerelde saklanır)

### 1. Depoyu Klonlayın ve Bağımlılıkları Yükleyin

```bash
git clone https://github.com/Cagrik34/microsoft-foundry-local-rag-assistant.git
cd microsoft-foundry-local-rag-assistant
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatın

```bash
python app.py
```

Başlangıçta interaktif mod seçim ekranı karşılayacaktır:

```text
╭─────────────────────────────────────────────────────────────╮
│  ⚡ ZENITH AI — Yerel RAG Akıllı Asistanı                   │
│  🔒 Tamamen Çevrimdışı • Gizli • Güvenli Yerel AI           │
├─────────────────────────────────────────────────────────────┤
│  🚀 Çalıştırma Modunu Seçin:                                │
│                                                             │
│   [1] 💻 Terminal (CLI) Modu                                │
│   [2] 🌐 Web Arayüzü (Streamlit — Tarayıcıda Açılır)        │
╰─────────────────────────────────────────────────────────────╯
```

---

## 📁 Proje Dizin Mimarisi

```text
microsoft-foundry-local-rag-assistant/
├── documents/                  # Belgelerin tutulduğu dizin (.md, .txt, .pdf, .docx, .xlsx, .pptx)
├── data/                       # Yerel SQLite vektör veritabanı (rag_knowledge.db)
├── src/                        # Modüler kaynak kodlar
│   ├── __init__.py             # Paket kök dizini
│   ├── config.py               # Yapılandırma sabitleri ve model seçimi
│   ├── core/                   # Çekirdek Yapay Zeka & RAG Motoru
│   │   ├── __init__.py         # Çekirdek paket tanımı
│   │   ├── models.py           # Thread-safe Foundry SDK yöneticisi & stateless istemci
│   │   ├── document_loader.py  # Çoklu format belge okuyucu & öbekleyici
│   │   ├── database.py         # SQLite vektör deposu & normalize kosinüs araması
│   │   └── engine.py           # RAG sorgu koordinatörü & tek çağrılı özetleyici
│   └── ui/                     # Kullanıcı arayüzleri
│       ├── __init__.py         # UI paket tanımı
│       ├── cli.py              # UTF-8 dayanıklı CLI terminali
│       └── web.py              # Streamlit Web UI (Web Speech TTS, Glassmorphism)
├── app.py                      # Ana giriş noktası (Entrypoint)
├── requirements.txt            # Python bağımlılıkları
├── README.md                   # Kurumsal İngilizce dokümantasyon
├── README.tr.md                # Kapsamlı Türkçe dokümantasyon
├── LICENSE                     # MIT Lisansı
└── .gitignore                  # Git hariç tutma kuralları
```

---

## 🛡️ Güvenlik ve Sıfır Veri Sızıntısı Mimarisi

- **%100 Çevrimdışı Çalışma:** Tüm yapay zeka ağırlıkları, vektör embedding'leri ve üretim hatları Microsoft Foundry Local SDK üzerinden yerel donanımda çalışır.
- **Sıfır Telemetri ve Bulut Çıkışı:** Hiçbir dış ağ isteği, API anahtarı veya üçüncü taraf bulut servisi kullanılmaz.
- **Bellek İçi Hijyen:** Streamlit sohbet oturumları ve önbellekler sadece yerel oturum belleğinde tutulur.

---

## 📜 Lisans & Telif Hakkı

Bu proje **MIT Lisansı** ile dağıtılmaktadır. Detaylar için [`LICENSE`](LICENSE) dosyasına bakınız.

**Yazar:** Çağrı Giray Keşan  
**Telif Hakkı:** © 2026 Çağrı Giray Keşan. Tüm Hakları Saklıdır.
