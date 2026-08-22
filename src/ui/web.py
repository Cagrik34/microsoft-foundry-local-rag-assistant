"""
Yerel RAG AI Asistanı — Modern Streamlit Web Arayüzü (src/ui/web.py)
===================================================================
Göz alıcı, modern ve kusursuz bir UI deneyimi sunan web arayüzü.
"""

import os
import sys
import io
import time
import threading
import streamlit as st

# Proje kök dizinini sys.path'e otomatik ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Projedeki .venv/site-packages dizinini sys.path'e otomatik ekle
venv_win = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages")
venv_unix = os.path.join(BASE_DIR, ".venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
if os.path.isdir(venv_win) and venv_win not in sys.path:
    sys.path.insert(0, venv_win)
elif os.path.isdir(venv_unix) and venv_unix not in sys.path:
    sys.path.insert(0, venv_unix)

# Windows terminal UTF-8 encoding ayarı
if sys.stdout and hasattr(sys.stdout, "encoding") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.config import DOCUMENTS_DIR, SUPPORTED_EXTENSIONS
from src.core.models import ModelManager
from src.core.database import VectorDatabase
from src.core.engine import RAGEngine

# ── Sayfa Yapılandırması ──
st.set_page_config(
    page_title="Zenith AI — Yerel RAG Asistanı",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Özel CSS (Gemini Live / Advanced Dalgalı & Modern UI) ──
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, #root, .stApp, .stAppContainer, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: linear-gradient(-45deg, #070913, #0f172a, #1e1b4b, #111827, #170d2b) !important;
    background-color: #070913 !important;
    background-size: 400% 400% !important;
    animation: geminiGradient 16s ease infinite !important;
    font-family: 'Inter', sans-serif;
}

@keyframes geminiGradient {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* 🌊 Streamlit Yükleme / Spinner Siyah Arka Planını Ezme */
[data-testid="stStatusWidget"],
.stSpinner,
div[data-baseweb="spinner"],
[data-testid="stMarkdownContainer"] {
    background: transparent !important;
    background-color: transparent !important;
}

/* 🔍 Sol Yan Bar (Sidebar) Tamamen Şeffaf & Kenarlıksız */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarHeader"],
[data-testid="stSidebarNav"] {
    background: transparent !important;
    background-color: transparent !important;
    border-right: none !important;
    box-shadow: none !important;
}

/* Streamlit Üst Header Şeffaflaştırma */
header[data-testid="stHeader"] {
    background: transparent !important;
    background-color: transparent !important;
}

/* 📤 File Uploader Dropzone Cam Efekti & Şeffaflık */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(15, 23, 42, 0.45) !important;
    border: 1.5px dashed rgba(168, 85, 247, 0.4) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #c084fc !important;
    background: rgba(15, 23, 42, 0.7) !important;
    box-shadow: 0 0 20px rgba(168, 85, 247, 0.25) !important;
}

[data-testid="stFileUploaderDropzone"] div,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    color: #cbd5e1 !important;
}

/* 💬 Chat Input (Soru Sorma Alanı) Glassmorphism & Alt Şerit Şeffaflaştırma */
[data-testid="stBottom"],
[data-testid="stBottom"] *,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] *,
footer,
footer * {
    background: transparent !important;
    background-color: transparent !important;
    border-top: none !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    padding-bottom: 1rem !important;
}

[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div[data-baseweb="base-input"],
[data-testid="stChatInput"] div[data-baseweb="input"] {
    background: rgba(15, 23, 42, 0.75) !important;
    background-color: rgba(15, 23, 42, 0.75) !important;
    border: 1px solid rgba(168, 85, 247, 0.4) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35) !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}

[data-testid="stChatInput"] > div:focus-within {
    border-color: #c084fc !important;
    box-shadow: 0 10px 35px rgba(168, 85, 247, 0.35) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    background-color: transparent !important;
    color: #f8fafc !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #94a3b8 !important;
}

/* 📚 Expander (Açılır Detay Kutuları) Cam Efekti */
[data-testid="stExpander"] {
    background: rgba(15, 23, 42, 0.45) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
}

/* 🌌 Işıltılı Renkli Dalgalı Işık Küreleri (Aura Orbs) */
.stApp::before {
    content: '';
    position: fixed;
    top: -15%;
    left: 10%;
    width: 700px;
    height: 700px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, rgba(168, 85, 247, 0.18) 40%, rgba(0,0,0,0) 70%);
    filter: blur(90px);
    border-radius: 50%;
    animation: floatOrb1 18s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

.stApp::after {
    content: '';
    position: fixed;
    bottom: -15%;
    right: 10%;
    width: 650px;
    height: 650px;
    background: radial-gradient(circle, rgba(236, 72, 153, 0.22) 0%, rgba(56, 189, 248, 0.2) 45%, rgba(0,0,0,0) 70%);
    filter: blur(100px);
    border-radius: 50%;
    animation: floatOrb2 22s ease-in-out infinite alternate;
    pointer-events: none;
    z-index: 0;
}

@keyframes floatOrb1 {
    0%   { transform: translate(0, 0) scale(1); }
    50%  { transform: translate(-90px, 70px) scale(1.2); }
    100% { transform: translate(110px, -50px) scale(0.9); }
}

@keyframes floatOrb2 {
    0%   { transform: translate(0, 0) scale(1.1); }
    50%  { transform: translate(80px, -60px) scale(0.85); }
    100% { transform: translate(-70px, 90px) scale(1.15); }
}

/* Ana Başlık Gradyanı */
.main-header {
    font-size: 2.3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 35%, #c084fc 70%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.5px;
}

.sub-header {
    color: #94a3b8;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
}

/* Gemini Dalga Çubuğu */
.gemini-wave-bar {
    height: 4px;
    width: 100%;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #f472b6, #38bdf8);
    background-size: 200% 100%;
    border-radius: 4px;
    animation: waveFlow 2s linear infinite;
    margin: 8px 0;
}

@keyframes waveFlow {
    0%   { background-position: 0% 0%; }
    100% { background-position: 200% 0%; }
}

/* Cam Efektli Kart Stilleri (Glassmorphism) */
.metric-card {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    padding: 14px 18px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    text-align: center;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.metric-value {
    font-size: 1.65rem;
    font-weight: 800;
    background: linear-gradient(135deg, #f8fafc, #cbd5e1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.metric-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
}

/* Kaynak Kartları */
.source-card {
    background: rgba(15, 23, 42, 0.65);
    border-left: 4px solid #a855f7;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 10px;
    font-size: 0.88rem;
    backdrop-filter: blur(12px);
    border-top: 1px solid rgba(255,255,255,0.05);
    border-right: 1px solid rgba(255,255,255,0.05);
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.source-title {
    font-weight: 600;
    color: #f1f5f9;
}

.similarity-badge {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(168, 85, 247, 0.25));
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.3);
    padding: 3px 10px;
    border-radius: 14px;
    font-weight: 700;
    font-size: 0.78rem;
    float: right;
}

/* Buton Özelleştirmeleri */
.stButton > button {
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35);
}

/* Yazıyor... Gösterge Stili */
.typing-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid rgba(168, 85, 247, 0.35);
    color: #c084fc;
    padding: 6px 14px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 8px;
}

.typing-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #c084fc;
    animation: pulseDot 1.2s infinite ease-in-out;
}

@keyframes pulseDot {
    0%, 100% { opacity: 0.2; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.2); }
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""


# ── Tam Ekran Çıkış Overlay Oluşturucu ──
def _build_exit_overlay(countdown: int) -> str:
    """Sayaç değerine göre tam ekran veda overlay'ini HTML olarak üretir."""
    if countdown > 0:
        subtitle = "Zenith AI güvenli şekilde kapatılıyor..."
        badge_text = "🔒 Kapanıyor"
        circle_bg = "linear-gradient(135deg, #6366f1, #a855f7)"
        circle_content = str(countdown)
    else:
        subtitle = "Zenith AI güvenli şekilde kapatıldı."
        badge_text = "🔒 Sekmeyi Güvenle Kapatabilirsiniz!"
        circle_bg = "linear-gradient(135deg, #10b981, #34d399)"
        circle_content = "✓"

    return (
        '<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;'
        "background:rgba(8,12,28,0.97);backdrop-filter:blur(20px);"
        "-webkit-backdrop-filter:blur(20px);z-index:2147483647;"
        'display:flex;align-items:center;justify-content:center;">'
        '<div style="background:#1e293b;border:1px solid rgba(168,85,247,0.35);'
        "border-radius:24px;padding:44px 52px;text-align:center;"
        "box-shadow:0 30px 60px -15px rgba(0,0,0,0.8),"
        '0 0 0 1px rgba(255,255,255,0.05);max-width:480px;">'
        '<div style="font-size:3rem;margin-bottom:12px;">👋</div>'
        '<div style="background:linear-gradient(135deg,#a855f7 0%,#ec4899 100%);'
        "-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
        "font-size:2.4rem;font-weight:800;margin:0 0 10px 0;"
        'letter-spacing:-0.5px;font-family:Inter,sans-serif;">'
        "Hoşça Kalın!</div>"
        f'<div style="color:#cbd5e1;font-size:1.05rem;margin-bottom:22px;'
        f'font-weight:500;font-family:Inter,sans-serif;">{subtitle}</div>'
        '<div style="display:inline-flex;align-items:center;gap:10px;'
        "background:rgba(15,23,42,0.7);color:#94a3b8;padding:10px 20px;"
        "border-radius:12px;font-size:0.88rem;"
        'border:1px solid rgba(255,255,255,0.07);font-family:Inter,sans-serif;">'
        f"{badge_text}"
        f'<span style="display:inline-flex;align-items:center;justify-content:center;'
        f"width:30px;height:30px;border-radius:50%;background:{circle_bg};"
        f'color:#fff;font-weight:700;font-size:0.95rem;font-family:Inter,sans-serif;">'
        f"{circle_content}</span>"
        "</div>"
        "</div></div>"
    )


@st.cache_resource
def get_rag_engine() -> RAGEngine:
    """Model yöneticisini ve veritabanını bir kez başlatır (Cache)."""
    model_mgr = ModelManager()
    try:
        model_mgr.initialize()
        model_mgr.load_embedding_model()
        model_mgr.load_chat_model()
    except Exception as e:
        print(f"⚠️ Model yükleme uyarısı: {e}")
    db = VectorDatabase()
    return RAGEngine(model_mgr, db)


def _render_tts_button(text: str, key_id: str) -> None:
    """Görme engelliler ve erişilebilirlik farkındalığı için yerel tarayıcı tabanlı Türkçe seslendirme (Web Speech API)."""
    import re
    clean_text = re.sub(r'[*#_`~>|\-\[\]\(\)\'\"\\\`]', ' ', text).replace('\n', ' ')
    clean_text = ' '.join(clean_text.split())

    if not clean_text or "Yanıt üretilemedi" in clean_text or "Operation was cancelled" in clean_text:
        return

    # Doğrudan tarayıcı olay tetikleyicisi (Streamlit yeniden yükleme gecikmesi olmadan 100% anında seslendirme)
    html_code = f"""
    <div style="margin-top: 6px; margin-bottom: 6px;">
        <button id="tts_btn_{key_id}" onclick="
            (function() {{
                try {{
                    var synth = window.top.speechSynthesis || window.speechSynthesis;
                    synth.cancel();
                    setTimeout(function() {{
                        var msg = new SpeechSynthesisUtterance('{clean_text}');
                        msg.lang = 'tr-TR';
                        msg.rate = 1.0;
                        synth.speak(msg);
                    }}, 80);
                }} catch(e) {{ console.error('TTS error:', e); }}
            }})();
        " style="
            background: linear-gradient(135deg, rgba(168,85,247,0.25), rgba(99,102,241,0.25));
            border: 1px solid rgba(168,85,247,0.4);
            color: #e2e8f0;
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
            text-align: center;
            font-family: 'Inter', sans-serif;
        " onmouseover="this.style.borderColor='#c084fc'; this.style.background='rgba(168,85,247,0.4)';" onmouseout="this.style.borderColor='rgba(168,85,247,0.4)'; this.style.background='linear-gradient(135deg, rgba(168,85,247,0.25), rgba(99,102,241,0.25))';">
            🔊 Yanıtı Seslendir (Görme Engelli Erişilebilirlik ve Farkındalık Desteği)
        </button>
    </div>
    """
    st.components.v1.html(html_code, height=48)


def _background_kill(delay: float = 0.3) -> None:
    """Modeller kapandıktan sonra Python sürecini işletim sistemi seviyesinde temiz bir şekilde kapatır."""
    time.sleep(delay)
    try:
        print("\n👋 Zenith AI sunucusu başarıyla kapatıldı. İyi günler!\n")
    except Exception:
        pass
    os._exit(0)


def handle_exit_flow(engine: RAGEngine) -> None:
    """
    Çıkış akışı:
    1) Şık veda ekranını gösterir.
    2) Modelleri bellekten güvenle boşaltır.
    3) JS ile tarayıcı sekmesini kapatır.
    4) 0.3s içinde Python sürecini işletim sistemi seviyesinde (os._exit) sonlandırır.
    """
    overlay_slot = st.empty()
    overlay_slot.markdown(_build_exit_overlay(0), unsafe_allow_html=True)

    # Modelleri bellekten boşalt
    try:
        engine.models.shutdown()
    except Exception:
        pass

    # JS ile sekmeyi kapat
    st.html("""
    <script>
        (function() {
            try { window.top.open('', '_self', ''); } catch(e) {}
            try { window.top.close(); } catch(e) {}
            try { window.close(); } catch(e) {}
            setTimeout(function() {
                try { window.top.location.href = 'about:blank'; } catch(e) {}
            }, 50);
        })();
    </script>
    """)

    # İşletim sistemi seviyesinde temiz ve anında çıkış
    _background_kill(0.3)


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Eğer çıkış yapılmışsa tekrar yüklemeyi engelle
    if st.session_state.get("app_exited"):
        st.markdown(
            _build_exit_overlay(0),
            unsafe_allow_html=True
        )
        st.html("""
        <script>
            try { window.top.open('', '_self', ''); } catch(e) {}
            try { window.top.close(); } catch(e) {}
            try { window.close(); } catch(e) {}
        </script>
        """)
        st.stop()
        return

    # RAG Motorunu al
    with st.spinner("⚡ Yapay zeka modelleri hazırlanıyor..."):
        engine = get_rag_engine()

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### ⚡ Zenith AI Studio")
        st.caption("Yerel ve Gizli RAG Asistanı")

        stats = engine.db.get_stats()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats['total_chunks']}</div>
                <div class="metric-label">Öbek (Chunk)</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats['total_files']}</div>
                <div class="metric-label">Dosya</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(
            f"<div style='text-align:center;margin-top:8px;font-size:0.8rem;color:#94a3b8;'>"
            f"💾 DB Boyutu: <b>{stats['db_size_mb']} MB</b></div>",
            unsafe_allow_html=True
        )
        st.divider()

        # Eylem Butonları
        st.markdown("##### ⚙️ Veritabanı Eylemleri")
        c1, c2 = st.columns(2)
        if c1.button("🔄 İndeksle", use_container_width=True, type="primary"):
            with st.spinner("📂 İndeksleniyor..."):
                try:
                    print("\n🔄 [Web UI] Belgeler veritabanına indeksleniyor...")
                except Exception:
                    pass
                res = engine.ingest_documents()
                if res["total_files"] == 0:
                    st.warning("⚠️ 'documents/' klasöründe belge bulunamadı.")
                else:
                    st.success(f"✅ {res['total_chunks']} öbek kaydedildi!")
                    try:
                        print(f"✅ [Web UI] {res['total_chunks']} öbek veritabanına kaydedildi.\n")
                    except Exception:
                        pass
                    st.rerun()

        if c2.button("🗑️ Temizle", use_container_width=True):
            deleted = engine.db.clear_all()
            try:
                print(f"🗑️ [Web UI] Veritabanı temizlendi ({deleted} öbek silindi).\n")
            except Exception:
                pass
            st.toast(f"Silindi: {deleted} öbek", icon="🗑️")
            st.rerun()

        st.divider()

        # ── Dosya Yükleme ──
        st.markdown("##### 📤 Dosya Yükle")
        uploaded_files = st.file_uploader(
            "Belgeleri buraya bırakın",
            type=[ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if uploaded_files:
            # Sadece yeni dosyaları kaydet (her rerun'da tekrar yazmayı engelle)
            if "uploaded_file_names" not in st.session_state:
                st.session_state.uploaded_file_names = set()

            current_names = {u.name for u in uploaded_files}
            new_files = [u for u in uploaded_files if u.name not in st.session_state.uploaded_file_names]

            if new_files:
                os.makedirs(DOCUMENTS_DIR, exist_ok=True)
                saved, skipped = [], []
                for u_file in new_files:
                    save_path = os.path.join(DOCUMENTS_DIR, u_file.name)
                    try:
                        with open(save_path, "wb") as f:
                            f.write(u_file.getbuffer())
                        saved.append(u_file.name)
                    except PermissionError:
                        skipped.append(u_file.name)
                    except Exception as e:
                        skipped.append(f"{u_file.name} ({e})")

                st.session_state.uploaded_file_names.update(saved)

                if saved:
                    st.toast(f"📥 {len(saved)} dosya kaydedildi!", icon="📥")
                if skipped:
                    st.warning(
                        f"⚠️ Şu dosyalar kaydedilemedi (açık veya kilitli — önce kapatın):\n"
                        + "\n".join(f"• {s}" for s in skipped)
                    )

            if st.button("🚀 Yüklenenleri İndeksle", use_container_width=True):
                with st.spinner("İndeksleniyor..."):
                    engine.ingest_documents()
                    st.success("İndeksleme tamamlandı!")
                    st.rerun()

        st.divider()

        # İndekslenmiş Dosya Listesi
        st.markdown("##### 📁 İndeksli Belgeler")
        if stats["files"]:
            for f_info in stats["files"]:
                st.markdown(
                    f"<div style='font-size:0.82rem;color:#cbd5e1;margin-bottom:4px;'>"
                    f"📄 <b>{f_info['name']}</b> "
                    f"<span style='color:#64748b;'>({f_info['chunks']} öbek)</span></div>",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Henüz belge indekslenmedi.")

        st.divider()

        # 📥 Sohbet Dışa Aktarma
        st.markdown("##### 📥 Sohbet Geçmişi")
        if st.session_state.get("messages"):
            chat_md = "# ⚡ Zenith AI — Sohbet Raporu\n\n"
            for m in st.session_state.messages:
                role_name = "🧑‍💻 Kullanıcı" if m["role"] == "user" else "⚡ Zenith AI"
                chat_md += f"### {role_name}\n{m['content']}\n\n"
                if m.get("sources"):
                    chat_md += "*📚 Doğrulanan Kaynaklar ve Benzerlik Skorları:*\n"
                    for s in m["sources"]:
                        sim_pct = int(s.get("similarity", 0) * 100)
                        chat_md += f"- **{s['source_file']}** (Bölüm {s['chunk_index'] + 1}) — `% {sim_pct} Benzerlik`\n"
                    chat_md += "\n"
                if m.get("search_time") is not None and m.get("gen_time") is not None:
                    chat_md += f"*⏱️ Arama: {m['search_time']}s | ⚡ Yanıt: {m['gen_time']}s*\n\n"
                chat_md += "---\n\n"

            st.download_button(
                label="📥 Sohbeti İndir (Markdown)",
                data=chat_md,
                file_name="zenith_ai_sohbet_raporu.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.caption("Henüz sohbet başlatılmadı.")

        st.divider()

        # 🔴 Çıkış
        st.markdown("##### 🚪 Sistem")
        if st.button("🔴 Uygulamayı Kapat ve Çık", key="exit_btn", use_container_width=True):
            st.session_state["app_exited"] = True
            handle_exit_flow(engine)

    # ── Ana Sohbet Alanı ──
    st.markdown('<div class="main-header">⚡ Zenith AI Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Kurumsal belgelerinizi tamamen çevrimdışı ve güvenli şekilde analiz edin.</div>',
        unsafe_allow_html=True
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Hızlı Örnek Sorular
    if not st.session_state.messages and engine.db.get_chunk_count() > 0:
        st.markdown("##### 💡 Hızlı Örnek Sorular")
        sample_questions = [
            "Projenin bütçesi ve mali analizi nedir?",
            "En sık karşılaşılan sorunlar ve çözümleri nelerdir?",
            "Teknik altyapı ve kullanılan teknolojileri özetle.",
        ]
        q_cols = st.columns(3)
        for idx, q_text in enumerate(sample_questions):
            if q_cols[idx].button(q_text, key=f"sq_{idx}", use_container_width=True):
                st.session_state.pending_question = q_text
                st.rerun()

    # Geçmiş Mesajlar
    for idx, message in enumerate(st.session_state.messages):
        avatar = "🧑‍💻" if message["role"] == "user" else "⚡"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                _render_tts_button(message["content"], f"hist_{idx}")
            if message.get("sources"):
                with st.expander("📚 Doğrulanan Kaynaklar ve Benzerlik Skorları"):
                    for src in message["sources"]:
                        st.markdown(
                            f'<div class="source-card">'
                            f'<span class="source-title">📄 {src["source_file"]}</span>'
                            f' (Bölüm {src["chunk_index"] + 1})'
                            f'<span class="similarity-badge">%{int(src["similarity"] * 100)}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
            if message.get("search_time") is not None and message.get("gen_time") is not None:
                st.markdown(
                    f'<div style="font-size:0.78rem;color:#94a3b8;margin-top:6px;display:inline-block;'
                    f'background:rgba(15,23,42,0.55);padding:4px 12px;border-radius:10px;'
                    f'border:1px solid rgba(168,85,247,0.25);">'
                    f'⏱️ <b>Arama:</b> {message["search_time"]}s &nbsp;|&nbsp; ⚡ <b>Yanıt:</b> {message["gen_time"]}s'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # Giriş
    pending_prompt = st.session_state.pop("pending_question", None)
    user_input = st.chat_input("Belgeleriniz hakkında bir soru yazın...")
    prompt = pending_prompt or user_input

    if prompt:
        if engine.db.get_chunk_count() == 0:
            st.warning("⚠️ Veritabanında henüz belge yok. Sol menüden belgelerinizi indeksleyin.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        try:
            print(f"\n🔍 [Web UI] Soru Alındı: '{prompt}'")
        except Exception:
            pass

        with st.chat_message("assistant", avatar="⚡"):
            t_gen_start = time.time()
            with st.spinner("⚡ Zenith AI belgeleri analiz ediyor ve yanıt hazırlıyor..."):
                stream_gen, sources, context, search_time = engine.query_stream(prompt)

            try:
                print(f"📎 [Web UI] {len(sources)} kaynak bulundu (Arama: {search_time}s)")
            except Exception:
                pass

            answer_placeholder = st.empty()
            full_answer = ""
            for chunk in stream_gen:
                full_answer += chunk
                answer_placeholder.markdown(full_answer + " ▌")
                time.sleep(0.01)

            answer_placeholder.markdown(full_answer)
            _render_tts_button(full_answer, "live")
            gen_time = round(time.time() - t_gen_start, 2)

            try:
                print(f"⚡ [Web UI] Yanıt Tamamlandı ({gen_time}s)\n")
            except Exception:
                pass

            sources_data = []
            if sources:
                sources_data = [
                    {
                        "source_file": s.source_file,
                        "chunk_index": s.chunk_index,
                        "similarity": s.similarity,
                    }
                    for s in sources
                ]
                with st.expander("📚 Doğrulanan Kaynaklar ve Benzerlik Skorları"):
                    for src in sources_data:
                        st.markdown(
                            f'<div class="source-card">'
                            f'<span class="source-title">📄 {src["source_file"]}</span>'
                            f' (Bölüm {src["chunk_index"] + 1})'
                            f'<span class="similarity-badge">%{int(src["similarity"] * 100)}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            st.markdown(
                f'<div style="font-size:0.78rem;color:#94a3b8;margin-top:6px;display:inline-block;'
                f'background:rgba(15,23,42,0.55);padding:4px 12px;border-radius:10px;'
                f'border:1px solid rgba(168,85,247,0.25);">'
                f'⏱️ <b>Arama:</b> {search_time}s &nbsp;|&nbsp; ⚡ <b>Yanıt:</b> {gen_time}s'
                f'</div>',
                unsafe_allow_html=True
            )

        st.session_state.messages.append({
            "role": "assistant",
            "content": full_answer,
            "sources": sources_data,
            "search_time": search_time,
            "gen_time": gen_time,
        })
        st.rerun()


if __name__ == "__main__":
    main()
