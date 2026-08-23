"""
Yerel RAG AI Asistanı — CLI Arayüzü (src/ui/cli.py)
===================================================
Kullanıcı komutlarını ve soru-cevap etkileşimini yöneten terminal modülü.
"""

import os
import sys
import io
import time
import subprocess

# Windows konsolunda UTF-8 desteği (emoji çökme koruması)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from typing import Optional
from src.config import DOCUMENTS_DIR, BASE_DIR
from src.core.models import ModelManager
from src.core.database import VectorDatabase
from src.core.engine import RAGEngine

# Windows konsolunda ANSI renk dizilimlerini etkinleştir
if os.name == "nt":
    os.system("")

# Terminal renk ve stil kodları (ANSI)
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

MODE_BANNER = f"""
{CYAN}=============================================================
  {MAGENTA}⚡ ZENITH AI{CYAN} — Kurumsal Yerel RAG Asistanı
  {DIM}🔒 Tamamen Çevrimdışı • Microsoft Foundry Local • 0 TL{RESET}
{CYAN}-------------------------------------------------------------
  {BOLD}🚀 Çalıştırma Modunu Seçin:{RESET}

   {GREEN}[1]{RESET} {BOLD}💻 Terminal (CLI) Modu{RESET}
   {GREEN}[2]{RESET} {BOLD}🌐 Web Uygulaması{RESET} {DIM}(React + FastAPI — Tarayıcıda Açılır){RESET}
{CYAN}============================================================={RESET}
"""

BANNER = f"""
{CYAN}=============================================================
  {MAGENTA}⚡ ZENITH AI STUDIO{CYAN} — Terminal Kontrol Paneli
  {DIM}🔒 Tamamen Çevrimdışı • Yerel RAG Yapay Zeka Motoru{RESET}
{CYAN}-------------------------------------------------------------
  {BOLD}📌 Kullanılabilir Komutlar:{RESET}
    {GREEN}/web{RESET}       — React + FastAPI Web Uygulamasını Başlat
    {GREEN}/indeksle{RESET}  — Belgeleri işle ve veritabanına kaydet
    {GREEN}/durum{RESET}     — Veritabanı durumunu ve istatistikleri göster
    {GREEN}/temizle{RESET}   — Veritabanı indeksini sıfırla
    {GREEN}/yardim{RESET}    — Kullanım kılavuzunu ve ipuçlarını göster
    {GREEN}/cikis{RESET}     — Uygulamadan güvenli şekilde çık

  {YELLOW}💬 Soru sormak için doğrudan yazıp Enter'a basın.{RESET}
{CYAN}============================================================={RESET}
"""

HELP_TEXT = f"""
{CYAN}📖 Zenith AI Kullanım Kılavuzu:{RESET}

1. Belgelerinizi '{DOCUMENTS_DIR}/' klasörüne yerleştirin (.md, .txt, .pdf, .docx, .xlsx, .pptx)
2. {GREEN}/indeksle{RESET} komutuyla belgeleri işleyin
3. Sorularınızı doğrudan yazın

Komutlar:
  {GREEN}/web{RESET}       — React + FastAPI Web Uygulamasını (tarayıcıda) başlatır.
  {GREEN}/indeksle{RESET}  — documents/ dizinindeki belgeleri okur, öbekler ve kaydeder.
  {GREEN}/durum{RESET}     — Veritabanındaki dosya ve öbek sayısını gösterir.
  {GREEN}/temizle{RESET}   — Tüm indekslenmiş verileri siler.
  {GREEN}/yardim{RESET}    — Bu kılavuzu gösterir.
  {GREEN}/cikis{RESET}     — Programdan çıkar.
"""


def launch_web_ui(model_manager: Optional[ModelManager] = None) -> None:
    """React + FastAPI web uygulamasını başlatır ve tarayıcıda açar.
    Bellek çakışmasını önlemek için CLI modelleri önce serbest bırakılır.
    """
    import webbrowser
    import threading

    if model_manager is not None:
        try:
            print("🔌 Web uygulaması için CLI modelleri serbest bırakılıyor...")
            model_manager.shutdown()
        except Exception:
            pass

    print("\n🌐 React + FastAPI Web Uygulaması Başlatılıyor...")
    print(f"🚀 Adres: http://localhost:8000")
    print("💡 Durdurmak için Ctrl+C tuşlarına basın.\n")

    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open("http://localhost:8000")
        except Exception:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        import uvicorn
        from src.api.server import app
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n🛑 Web uygulaması kapatıldı.\n")
    except Exception as e:
        print(f"\n❌ Web uygulaması başlatılamadı: {e}\n")
    finally:
        if model_manager is not None:
            try:
                print("🔄 CLI modelleri yeniden başlatılıyor...")
                model_manager.initialize()
            except Exception:
                pass


def handle_index(engine: RAGEngine) -> None:
    """Belgeleri tarar ve indeksleme sürecini başlatır."""
    print(f"\n📂 '{DOCUMENTS_DIR}' dizini taranıyor...\n")
    result = engine.ingest_documents()
    if result["total_files"] == 0:
        print(f"\n💡 İpucu: '{DOCUMENTS_DIR}' dizinine belgeler ekleyin.")


def handle_status(db: VectorDatabase) -> None:
    """Veritabanındaki dosya ve öbek (chunk) durumunu gösterir."""
    stats = db.get_stats()
    print("\n📊 Veritabanı Durumu:")
    print(f"   Toplam dosya  : {stats['total_files']}")
    print(f"   Toplam chunk  : {stats['total_chunks']}")
    print(f"   DB boyutu     : {stats['db_size_mb']} MB")

    if stats["files"]:
        print("\n   Dosyalar:")
        for f in stats["files"]:
            print(f"     • {f['name']} — {f['chunks']} chunk")
    print()


def handle_clear(db: VectorDatabase) -> None:
    """Veritabanındaki tüm indeks verilerini temizler."""
    count = db.get_chunk_count()
    if count == 0:
        print("\n📭 Veritabanı zaten boş.\n")
        return

    confirm = input(f"\n⚠️  {count} chunk silinecek. Emin misiniz? (e/h): ").strip().lower()
    if confirm in ("e", "evet"):
        deleted = db.clear_all()
        print(f"🗑️  {deleted} chunk silindi. Veritabanı temizlendi.\n")
    else:
        print("❌ İptal edildi.\n")


def handle_query(engine: RAGEngine, question: str) -> None:
    """Kullanıcı sorusunu alarak RAG motoru üzerinden canlı akış (streaming) ile yanıtlar."""
    if engine.db.get_chunk_count() == 0:
        print("\n⚠️  Veritabanında henüz belge yok.")
        print("   Önce /indeksle komutuyla belgelerinizi indeksleyin.\n")
        return

    print("\n🔍 Aranıyor...")
    stream_gen, sources, context, search_time = engine.query_stream(question)

    if sources:
        similarities = ", ".join(f"{s.similarity:.2f}" for s in sources)
        print(f"   📎 {len(sources)} kaynak bulundu (benzerlik: {similarities})")

    print("\n🤖 Yanıt:\n")
    t_gen_start = time.time()
    for chunk in stream_gen:
        sys.stdout.write(chunk)
        sys.stdout.flush()
    gen_time = round(time.time() - t_gen_start, 2)
    print("\n")

    print(f"⏱️  Hibrit Arama: {search_time}s | ⚡ Çıkarım: {gen_time}s")

    if sources:
        print("\n📚 Doğrulanan Kaynaklar ve Alaka Düzeyleri:")
        for src in sources:
            print(f"   • [{src.citation_index}] {src.source_file}, Bölüm {src.chunk_index + 1} (Alaka: %{src.relevance_percentage} | Eşleşme: {src.match_type.upper()})")
    print()


def run_cli() -> None:
    """Ana CLI döngüsünü ve başlangıç mod seçimini çalıştırır."""
    print(MODE_BANNER)
    while True:
        try:
            mode_choice = input("Seçiminiz (1 veya 2) [Varsayılan: 1]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Güle güle!")
            sys.exit(0)

        if mode_choice == "" or mode_choice == "1":
            break
        elif mode_choice == "2":
            launch_web_ui()
            sys.exit(0)
        else:
            print("⚠️  Hatalı seçim yaptınız! Lütfen 1 veya 2 giriniz (veya Enter'a basın).\n")

    print(BANNER)
    print("🚀 Sistem başlatılıyor...\n")

    model_manager = ModelManager()
    try:
        model_manager.initialize()
    except Exception as e:
        print(f"\n❌ SDK başlatılamadı: {e}")
        print("Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.")
        sys.exit(1)

    db = VectorDatabase()
    engine = RAGEngine(model_manager, db)

    if not os.path.isdir(DOCUMENTS_DIR):
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        print(f"📁 '{DOCUMENTS_DIR}' dizini oluşturuldu.\n")

    chunk_count = db.get_chunk_count()
    if chunk_count > 0:
        print(f"📊 Veritabanında {chunk_count} chunk mevcut. Soru sormaya başlayabilirsiniz.\n")
    else:
        print("💡 Başlamak için belgelerinizi 'documents/' dizinine ekleyin ve /indeksle komutunu çalıştırın.\n")

    try:
        while True:
            try:
                user_input = input("❓ > ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if not user_input:
                continue

            command = user_input.lower()

            if command in ("/cikis", "/çıkış", "/exit", "/quit"):
                break
            elif command in ("/web", "/gui", "/browser"):
                launch_web_ui(model_manager)
            elif command in ("/indeksle", "/index"):
                handle_index(engine)
            elif command in ("/durum", "/status"):
                handle_status(db)
            elif command in ("/temizle", "/clear"):
                handle_clear(db)
            elif command in ("/yardim", "/yardım", "/help"):
                print(HELP_TEXT)
            elif command.startswith("/"):
                print(f"⚠️  Bilinmeyen komut: {command}")
                print("   /yardim yazarak kullanılabilir komutları görün.\n")
            else:
                handle_query(engine, user_input)
    finally:
        try:
            model_manager.shutdown()
        except Exception:
            pass
        print("👋 Güle güle!")


if __name__ == "__main__":
    run_cli()
