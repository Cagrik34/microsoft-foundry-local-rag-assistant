# ⚡ Zenith AI — Yerel ve Gizli RAG Asistanı (Enterprise Local RAG)

Tamamen çevrimdışı, sıfır veri sızıntısı riskiyle çalışan kurumsal belge tabanlı Soru-Cevap (RAG - Retrieval-Augmented Generation) asistanı.  
**Microsoft Foundry Local SDK** altyapısını kullanarak yerel `phi-3.5-mini` (3.8B) LLM ve `qwen3-embedding-0.6b` (1024-dim) modellerini yüksek performansla çalıştırır. Hiçbir dış internet bağlantısı, API anahtarı veya bulut servisi gerektirmez.

---

## 🎯 Projenin Amacı ve Sosyal Farkındalık Vizyonu

> *"Yapay zeka teknolojisi yalnızca belirli bir gruba değil, engelleri ve imkânları ne olursa olsun **her insana** hitap edebilmeli, eşit ve engelsiz şekilde erişilebilmelidir."*

**Zenith AI** projesinin temel amacı; en ileri yapay zeka ve RAG teknolojilerini sadece güçlü bir yazılım mimarisi olarak sunmak değil, aynı zamanda **görme engelli bireyler başta olmak üzere toplumun tüm kesimlerine hitap eden evrensel bir erişilebilirlik ve farkındalık modeli** oluşturmaktır.

- **♿ Görme Engelliler İçin Engelsiz Bilgi:** Tüm yapay zeka yanıtlarını tek tıkla (%100 çevrimdışı ve gizli) seslendiren tarayıcı motoru entegrasyonu ile görme engelli bireylerin bilgiye erişimindeki engeller kaldırılmıştır.
- **🌍 Her İnsana Hitap Eden Fırsat Eşitliği:** Bulut abonelikleri, pahalı sunucular veya internet bağlantısı zorunluluğunu ortadan kaldırarak; bilgiye erişimi her birey için tamamen ücretsiz, gizli ve eşit kılmayı hedefler.

---

## ✨ Öne Çıkan Özellikler

- 🔒 **%100 Çevrimdışı ve Gizli (Zero Data Leakage):** Verileriniz ve dokümanlarınız cihazınızdan asla dışarı çıkmaz.
- 🔊 **Görme Engelli Erişilebilirlik ve Farkındalık Desteği (Web Speech TTS):** Yapay zeka yanıtlarını tarayıcının yerel Türkçe ses motoruyla (%100 çevrimdışı, sıfır dış bağımlılık) sesli olarak okuyan erişilebilirlik ve sosyal farkındalık mekanizması.
- 🌊 **Canlı Yanıt Akışı (Live Streaming Response):** Yanıtı tek seferde bekletmeden, ChatGPT/Gemini stili canlı kelime akışı (`▌` imleci ile hem Web UI hem CLI desteği).
- **🌐 Çift Modlu Çalışma Mimarisi (Dual-Mode):**
  - **Gemini Live / Advanced Stili Web Panel (`src/ui/web.py`):** Dalgalı hareketli gradient arka plan, cam efektli (glassmorphic) şeffaf yan panel ve sürükle-bırak dosya yükleme.
  - **Hızlı Terminal CLI (`app.py`):** Hızlı ve tüy hafifliğinde komut satırı sohbet arayüzü.
- **📁 Çoklu Doküman Format Desteği:** Markdown (`.md`), Düz Metin (`.txt`), PDF (`.pdf`), Word (`.docx`), Excel (`.xlsx`), PowerPoint (`.pptx`).
- **📤 Gelişmiş Dosya Yükleme:** Sürükle-bırak yöntemiyle doğrudan tarayıcıdan belge ekleme, kilitli/açık dosya hata yönetimi (`PermissionError`) ve otomatik vektörleştirme.
- **⚡ Akıllı Kaynak ve Benzerlik Doğrulama:** Üretilen her yanıtın altında bilginin alındığı kaynak dosya adı, bölüm numarası, `%85` gibi yüzdelik benzerlik etiketleri ve süre metrikleri.
- **🚪 İşletim Sistemi Seviyesinde Temiz Kapanış:** Çıkış yapıldığında modelleri RAM'den boşaltan ve 0.3 saniyede `os._exit(0)` ile terminali anında serbest bırakan kapatma mekanizması.
- **💾 SQLite Vektör Deposu:** Ekstra veritabanı sunucusu gerektirmeyen, hafif ve yerel SQLite vektör veritabanı (`rag_knowledge.db`).
- **📥 Benzerlik Oranlı Sohbet Raporu İndirme (Export Chat):** Web panelinden sohbet oturumunu benzerlik yüzdeleri ve süre metrikleri ile Markdown raporu olarak tek tıkla indirebilme.

---

## 🏗️ Sistem Mimarisi ve Mühendislik Tasarımı

```text
                               ┌────────────────────────────────────────┐
                               │     Kullanıcı Arayüzü (UI Layer)      │
                               │  [Web (Streamlit)]  |  [Terminal CLI]  │
                               └───────────────────┬────────────────────┘
                                                   │ (Event Dispatch)
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │      RAG Orkestrasyon Motoru           │
                               │           (src/core/engine.py)         │
                               └─────────┬────────────────────┬─────────┘
                                         │                    │
                    (Vektör Arama)       │                    │ (Metin İstemcisi)
                                         ▼                    ▼
             ┌───────────────────────────────────┐    ┌───────────────────────────────────┐
             │ SQLite Vektör Deposu (database.py)│    │ Model Yöneticisi (src/core/models)│
             │   - Kosinüs Benzerliği            │    │   - ThreadPoolExecutor İzolasyonu │
             │   - 1024-Boyut Matris Çarpımı     │    │   - Stateless ChatClient Üretimi  │
             └───────────────────────────────────┘    └─────────────────┬─────────────────┘
                                                                        │ (C++ Native gRPC)
                                                                        ▼
                                                      ┌───────────────────────────────────┐
                                                      │    Microsoft Foundry Local SDK    │
                                                      │  - qwen3-embedding-0.6b (1024-d)  │
                                                      │  - phi-3.5-mini (3.8B Instruct)   │
                                                      └───────────────────────────────────┘
```

---

## 🛠️ Teknik Darboğazlar ve Çözüm Mimarisi (Architectural Breakthroughs)

Proje geliştirme sürecinde tespit edilen **kritik sistem darboğazları ve uygulanan mühendislik çözümleri** aşağıda açıklanmıştır:

### 1. Streamlit AsyncIO Event Loop & C++ gRPC Thread Kilitlenmesi (Deadlock)
* **Darboğaz:** Microsoft Foundry SDK'nın C++ gRPC istemcisi, Streamlit'in `asyncio` event loop'u çalışırken ana Python iş parçacığından senkron çağrıldığında event loop gRPC kanalını kilitliyordu (thread starvation). Bu durum yanıtların 180s boyunca donmasına ve `Operation was cancelled` hatasına yol açıyordu.
* **Çözüm:** `src/core/models.py` içerisinde `chat_complete` ve `generate_embedding` metodları `concurrent.futures.ThreadPoolExecutor(max_workers=1)` ile izole bir işletim sistemi iş parçacığına taşındı. C++ gRPC çağrıları AsyncIO döngüsünden tamamen bağımsız hale getirilerek kilitlenme çözüldü.

### 2. Oturumlar Arası Bağlam Şişmesi (Session Memory Leak / Context Accumulation)
* **Darboğaz:** `ChatClient` nesnesi uzun süreli oturumlarda arka arkaya yapılan sorgularda eski sohbet geçmişini ve bağlamları hafızasında tutmaya devam ediyordu. 2. ve 3. sorularda bağlam boyutu 4.800+ karaktere ulaşıp CPU'yu kilitliyordu.
* **Çözüm:** `chat_complete` içerisinde her yeni RAG sorgusu için `self._chat_model.get_chat_client()` ile **durumsuz (stateless)** temiz bir istemci nesnesi üretilmesi sağlandı. Bağlam boyutu sabit tutularak bellek şişmesi engellendi.

### 3. C++ Native gRPC 120.0s RPC Zaman Aşımı Sınırı
* **Darboğaz:** Microsoft Foundry SDK'nın native C++ katmanında `complete_chat` için 120.0 saniyelik sabit bir RPC kuralı vardı. 7B modeller CPU üzerinde ağır metinlerde 120s duvarına çarpıyordu.
* **Çözüm:** Model katmanında Microsoft'un yüksek hızlı **`phi-3.5-mini`** (3.8B Instruct) modeline geçildi. CPU ön-işleme (prefill) ve yanıt süresi **0.24s - 15s** seviyesine düşürülerek 120s zaman aşımı riski tamamen ortadan kaldırıldı.

### 4. Kapanış Esnasında Terminal Asılı Kalması (`RuntimeError: Event loop is closed`)
* **Darboğaz:** Streamlit `st.stop()` çağrıldığında AsyncIO event loop'unu kapatıyor, ancak arka plandaki zamanlayıcı döngüsü kapalı loop'a erişmeye çalışıp terminali kilitliyordu.
* **Çözüm:** `src/ui/web.py` içerisindeki çıkış akışı `_background_kill(0.3)` ile **0.3 saniye içinde `os._exit(0)`** çağrısına yönlendirildi. İşletim sistemi seviyesinde temiz çıkış sağlanarak terminal anında serbest bırakıldı.

---

## ⚙️ Teknik Parametreler ve RAG Ayarları

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| **Embedding Modeli** | `qwen3-embedding-0.6b` | Türkçe ve çok dilli vektörleştirme (~600 MB, 1024 boyut) |
| **Chat Modeli** | `phi-3.5-mini` | Microsoft'un yüksek hızlı yerel Instruct dil modeli (~2.2 GB, 3.8B) |
| **Öbek Uzunluğu (Chunk Size)** | `1000` karakter | Anlamsal bütünlük sağlayan parçalama sınırı |
| **Öbek Örtüşmesi (Overlap)** | `200` karakter | Parçalar arası bağlam kopmasını önleyen örtüşme |
| **Benzerlik Eşiği (Similarity)** | `0.05` | Kosinüs benzerliği kabul eşiği |
| **Arama Limiti (Top-K)** | `3` öbek | Yanıta dahil edilen en yüksek puanlı öbek sayısı |
| **Bağlam Limiti (Max Context)** | `1600` karakter | LLM'e beslenen maksimum zengin bağlam boyutu (12-15s hızlı CPU yanıtı) |
| **Max Tokens** | `256` token | Üretilebilecek maksimum yanıt jeton sınırı |

---

## 🛠️ Gereksinimler ve Kurulum

- **İşletim Sistemi:** Windows 10/11
- **Python:** 3.11 veya üstü
- **RAM:** Minimum 8 GB (16 GB önerilir)
- **Disk Alanı:** ~3 GB (Modeller ilk çalıştırmada bir kez indirilir ve yerelde saklanır)

### 1. Bağımlılıkları Yükleyin

```bash
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

Seçiminiz (1 veya 2) [Varsayılan: 1]:
```

* **`1` veya Enter:** Terminal CLI modunda çalışmayı başlatır.
* **`2`:** Otomatik olarak tarayıcıyı açar ve **Gemini Live stili Web Paneli** başlatır.
* *(Doğrudan Web arayüzünü çalıştırmak için `streamlit run src/ui/web.py` komutu da kullanılabilir.)*

---

## 📖 Kullanım ve Komutlar

1. Belgelerinizi `documents/` klasörüne ekleyin (veya Web panelinden sürükleyip bırakın).
2. `/indeksle` komutuyla (veya Web panelindeki **🔄 İndeksle** butonuyla) belgeleri veritabanına kaydedin.
3. Sorularınızı sormaya başlayın!

### 💻 Terminal (CLI) Komutları

| Komut | Açıklama |
|-------|----------|
| `/web` | Streamlit Web Arayüzünü tarayıcıda başlatır. |
| `/indeksle` | `documents/` dizinindeki belgeleri okur, öbeklere böler ve vektör veritabanına kaydeder. |
| `/durum` | Veritabanı durumunu, dosya ve öbek (chunk) sayılarını gösterir. |
| `/temizle` | İndekslenmiş tüm verileri veritabanından siler. |
| `/yardim` | Kullanım kılavuzunu gösterir. |
| `/cikis` | Programdan çıkar ve modelleri RAM'den boşaltır. |

---

## 📂 Proje Dizin Mimarisi

```text
microsoft-foundry-local-rag-assistant/
├── documents/                  # Belgelerin tutulduğu ana dizin (.md, .pdf, .docx, .xlsx vb.)
├── data/                       # SQLite veritabanı (rag_knowledge.db)
├── src/                        # ⚡ Modüler Kaynak Kod Klasörü
│   ├── __init__.py             # Python paket tanımlayıcısı
│   ├── config.py               # Yapılandırma sabitleri ve model ayarları
│   ├── core/                   # Çekirdek Yapay Zeka & RAG Motoru
│   │   ├── __init__.py         # Çekirdek paket tanımlayıcısı
│   │   ├── models.py           # Thread-safe Foundry Model Yöneticisi & Stateless Client
│   │   ├── document_loader.py  # Çoklu belge okuyucuları & metin öbekleme (Chunking)
│   │   ├── database.py         # SQLite Vektör Veritabanı & Kosinüs Benzerliği
│   │   └── engine.py           # RAG Orkestrasyon Motoru & Arama Akışı
│   └── ui/                     # Kullanıcı Arayüzleri
│       ├── __init__.py         # Arayüz paket tanımlayıcısı
│       ├── cli.py              # Terminal CLI arayüzü & Benzerlik Skorlu Çıktı
│       └── web.py              # Modern Streamlit Web Arayüzü (Gemini Live Stili)
├── app.py                      # Ana Uygulama Başlatıcısı (Entrypoint)
├── requirements.txt            # Proje bağımlılıkları
├── README.md                   # Kapsamlı Dokümantasyon
├── LICENSE                     # MIT Lisans Dosyası
└── .gitignore                  # Git yoksayma kuralları
```

---

## 📄 Lisans

Bu proje **MIT Lisansı** altında lisanslanmıştır.

```text
MIT License

Copyright (c) 2026 Çağrı Giray Keşan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
