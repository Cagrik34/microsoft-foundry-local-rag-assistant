"""
Zenith AI — SOTA Kurumsal Yerel RAG Web Arayüzü (src/ui/web.py)
===============================================================
Microsoft Foundry Local SDK ile çalışan; Hibrit Arama (Dense + BM25 RRF),
İnteraktif Cümle İçi Alıntılar ([1], [2]), Sesli Asistan (STT/TTS) ve
Çoklu Sohbet Oturumu (Multi-Session) destekli kurumsal analiz paneli.
"""

import os
import sys
import time
import re
import json
import streamlit as st

# Proje kök dizinini sys.path'e ekle
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Sanal ortam paketlerini ekle
venv_win = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages")
venv_unix = os.path.join(BASE_DIR, ".venv", "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages")
if os.path.isdir(venv_win) and venv_win not in sys.path:
    sys.path.insert(0, venv_win)
elif os.path.isdir(venv_unix) and venv_unix not in sys.path:
    sys.path.insert(0, venv_unix)

# Windows konsol UTF-8 ayarı
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.config import DOCUMENTS_DIR, SUPPORTED_EXTENSIONS, CHAT_MODEL, EMBEDDING_MODEL
from src.core.models import ModelManager
from src.core.database import VectorDatabase
from src.core.engine import RAGEngine

# ── Sayfa Yapılandırması ──
st.set_page_config(
    page_title="Zenith AI — Kurumsal Yerel RAG Asistanı",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Kurumsal Düzey Dark-Mode UI / UX CSS ──
MODERN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #080b14 !important;
    color: #f1f5f9 !important;
}

/* Arka Plan Ambient Gradient */
.stApp {
    background: radial-gradient(circle at 15% 15%, rgba(37, 99, 235, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
                #080b14 !important;
}

/* Sidebar Tasarımı */
[data-testid="stSidebar"] {
    background-color: #0d1322 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}

[data-testid="stSidebarContent"] {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
}

/* Üst Başlık & Header */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Kartlar ve Metrikler */
.stat-card {
    background: rgba(17, 24, 39, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 10px 12px;
    text-align: center;
    backdrop-filter: blur(10px);
}

.stat-value {
    font-size: 1.4rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.2;
}

.stat-label {
    font-size: 0.7rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 3px;
}

/* Canlı Durum Rozeti */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #34d399;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 500;
}

.status-dot {
    width: 6px;
    height: 6px;
    background-color: #10b981;
    border-radius: 50%;
    animation: pulseDot 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulseDot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
}

/* Hero Başlık Alanı */
.hero-container {
    padding: 0.2rem 0 1.2rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    margin-bottom: 1.2rem;
}

.hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 10px;
}

.hero-subtitle {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-top: 4px;
}

/* İnteraktif Cümle İçi Alıntı Rozetleri [1], [2] */
.citation-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.45);
    color: #c7d2fe;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 6px;
    margin: 0 3px;
    vertical-align: baseline;
    cursor: default;
    transition: all 0.2s ease;
}

.citation-pill:hover {
    background: rgba(99, 102, 241, 0.4);
    border-color: #818cf8;
    color: #ffffff;
    transform: translateY(-1px);
}

/* Kaynak Alıntı Kartları */
.source-item {
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-left: 3px solid #6366f1;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 8px;
    font-size: 0.84rem;
}

.source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.source-name {
    font-weight: 600;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 8px;
}

.source-score {
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
    padding: 2px 8px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.75rem;
}

.source-preview {
    color: #cbd5e1;
    font-size: 0.78rem;
    margin-top: 8px;
    line-height: 1.45;
    background: rgba(8, 12, 20, 0.6);
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.03);
}

/* Telemetri Çubuğu */
.telemetry-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    color: #94a3b8;
    background: rgba(15, 23, 42, 0.6);
    padding: 4px 10px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    margin-top: 8px;
}

/* Oturum Geçmişi Menü Öğesi */
.session-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    border-radius: 8px;
    background: rgba(17, 24, 39, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 6px;
    font-size: 0.8rem;
    color: #cbd5e1;
    transition: all 0.2s ease;
}

.session-item:hover {
    background: rgba(30, 41, 59, 0.7);
    border-color: rgba(99, 102, 241, 0.3);
}

/* Chat Input Kutusu */
[data-testid="stChatInput"] {
    background-color: transparent !important;
    border-top: none !important;
    padding-bottom: 1.2rem !important;
}

[data-testid="stChatInput"] > div {
    background-color: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

[data-testid="stChatInput"] > div:focus-within {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2), 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
}

/* Butonlar */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    padding: 6px 12px !important;
    transition: all 0.2s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.stButton > button:hover {
    border-color: rgba(99, 102, 241, 0.4) !important;
    background-color: rgba(30, 41, 59, 0.8) !important;
}

/* File Uploader */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1px dashed rgba(255, 255, 255, 0.15) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #6366f1 !important;
    background: rgba(15, 23, 42, 0.8) !important;
}

@keyframes loadingBar {
    0% { transform: translateX(-100%); }
    50% { transform: translateX(50%); width: 70%; }
    100% { transform: translateX(200%); }
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""


# ── Çıkış Arayüzü ──
def _render_exit_screen() -> None:
    """Temiz ve kurumsal kapanış ekranı."""
    st.html("""
    <div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:#080b14;
                display:flex;align-items:center;justify-content:center;z-index:999999;">
        <div style="background:#0f172a;border:1px solid rgba(255,255,255,0.08);border-radius:16px;
                    padding:36px 44px;text-align:center;max-width:440px;box-shadow:0 20px 40px rgba(0,0,0,0.6);">
            <div style="font-size:2rem;margin-bottom:8px;">⚡</div>
            <div style="font-size:1.4rem;font-weight:700;color:#f8fafc;margin-bottom:6px;">Zenith AI Kapatıldı</div>
            <div style="font-size:0.88rem;color:#94a3b8;margin-bottom:20px;">
                Tüm yerel yapay zeka modelleri bellekten güvenle kaldırıldı. Bu sekmeyi kapatabilirsiniz.
            </div>
            <div style="display:inline-block;padding:6px 14px;border-radius:8px;background:rgba(16,185,129,0.1);
                        color:#34d399;font-size:0.8rem;border:1px solid rgba(16,185,129,0.2);">
                ✓ Oturum Güvenle Sonlandırıldı
            </div>
        </div>
    </div>
    """)


def _background_exit(delay: float = 0.3) -> None:
    """Süreci işletim sistemi düzeyinde sonlandırır."""
    time.sleep(delay)
    os._exit(0)


def handle_exit_flow(engine: RAGEngine) -> None:
    """Modelleri boşaltır ve güvenli çıkış yapar."""
    try:
        engine.models.shutdown()
    except Exception:
        pass
    _render_exit_screen()
    _background_exit(0.3)


@st.cache_resource(show_spinner=False)
def get_rag_engine() -> RAGEngine:
    """Model yöneticisini ve hibrit veritabanını bir kez başlatır (Cache)."""
    model_mgr = ModelManager()
    try:
        model_mgr.initialize()
        model_mgr.load_embedding_model()
        model_mgr.load_chat_model()
    except Exception as e:
        print(f"⚠️ Model hazırlığı uyarısı: {e}")
    db = VectorDatabase()
    return RAGEngine(model_mgr, db)


def format_in_text_citations(text: str) -> str:
    """Metin içindeki [1], [2] alıntılarını şık rozetlere dönüştürür."""
    if not text:
        return text
    # [1], [2], [1, 2] kalıplarını bul ve citation-pill sınıfıyla sar
    def _replace_citation(match):
        num = match.group(1)
        return f'<span class="citation-pill">[{num}]</span>'

    return re.sub(r'\[(\d+)\]', _replace_citation, text)


def _render_action_bar(text: str, key_id: str) -> None:
    """Web Speech API ile seslendirme ve mikrofon araç çubuğu."""
    clean_text = re.sub(r'[*#_`~>|\-\[\]\(\)\'\"\\\`]', ' ', text).replace('\n', ' ')
    clean_text = ' '.join(clean_text.split())

    if not clean_text or "Bu bilgi belgelerde" in clean_text or "Yanıt üretilemedi" in clean_text:
        return

    html_code = f"""
    <div style="display:flex;align-items:center;gap:10px;margin-top:8px;">
        <button id="tts_btn_{key_id}" onclick="
            (function() {{
                try {{
                    var synth = window.top.speechSynthesis || window.speechSynthesis;
                    if (synth.speaking) {{
                        synth.cancel();
                        return;
                    }}
                    var msg = new SpeechSynthesisUtterance('{clean_text}');
                    msg.lang = 'tr-TR';
                    msg.rate = 1.0;
                    synth.speak(msg);
                }} catch(e) {{ console.error('TTS error:', e); }}
            }})();
        " style="
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #cbd5e1;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s ease;
        " onmouseover="this.style.borderColor='rgba(99,102,241,0.4)'; this.style.color='#f8fafc';"
           onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'; this.style.color='#cbd5e1';">
            🔊 Seslendir
        </button>
    </div>
    """
    if hasattr(st, "html"):
        st.html(html_code)
    else:
        st.components.v1.html(html_code, height=36)


def _render_voice_mic_widget() -> None:
    """Sesli Soru Sorma (Web Speech Recognition STT Mikrofon Butonu)."""
    mic_html = """
    <div style="margin-top: 6px; margin-bottom: 12px;">
        <button id="stt_mic_btn" style="
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #cbd5e1;
            padding: 7px 14px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s ease;
            width: 100%;
            justify-content: center;
        " onmouseover="this.style.borderColor='rgba(99,102,241,0.4)'; this.style.color='#f8fafc';"
           onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'; this.style.color='#cbd5e1';">
            🎙️ Sesli Soru Sor (Mikrofon)
        </button>
    </div>
    <script>
    (function() {
        var btn = document.getElementById('stt_mic_btn');
        if (!btn) return;
        btn.onclick = function() {
            var SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition || (window.top && (window.top.SpeechRecognition || window.top.webkitSpeechRecognition));
            if (!SpeechRec) {
                alert('Tarayıcınız Web Speech ses tanıma desteği sunmuyor. Lütfen Edge veya Chrome kullanın.');
                return;
            }
            try {
                var rec = new SpeechRec();
                rec.lang = 'tr-TR';
                rec.continuous = false;
                rec.interimResults = false;

                btn.style.background = 'rgba(239, 68, 68, 0.25)';
                btn.style.borderColor = '#ef4444';
                btn.innerHTML = '🔴 Dinleniyor... (Konuşun)';

                rec.onresult = function(e) {
                    var text = e.results[0][0].transcript;
                    var doc = (window.top && window.top.document) ? window.top.document : document;
                    var chatInputs = doc.querySelectorAll('textarea[data-testid="stChatInputTextArea"]');
                    if (chatInputs.length > 0) {
                        var inp = chatInputs[chatInputs.length - 1];
                        inp.value = text;
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    btn.style.background = 'rgba(30, 41, 59, 0.6)';
                    btn.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    btn.innerHTML = '🎙️ Sesli Soru Sor (Mikrofon)';
                };

                rec.onerror = function() {
                    btn.style.background = 'rgba(30, 41, 59, 0.6)';
                    btn.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    btn.innerHTML = '🎙️ Sesli Soru Sor (Mikrofon)';
                };

                rec.onend = function() {
                    btn.style.background = 'rgba(30, 41, 59, 0.6)';
                    btn.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    btn.innerHTML = '🎙️ Sesli Soru Sor (Mikrofon)';
                };

                rec.start();
            } catch(e) {
                console.error('STT hatası:', e);
            }
        };
    })();
    </script>
    """
    if hasattr(st, "html"):
        st.html(mic_html)
    else:
        st.components.v1.html(mic_html, height=44)


def main() -> None:
    st.markdown(MODERN_CSS, unsafe_allow_html=True)

    if st.session_state.get("app_exited"):
        _render_exit_screen()
        st.stop()
        return

    # RAG Motorunu yükle (Kurumsal Açılış Ekranı)
    splash_slot = st.empty()
    if "models_loaded" not in st.session_state:
        splash_slot.markdown(
            f"""
            <div style="background:rgba(15,23,42,0.8);border:1px solid rgba(255,255,255,0.08);
                        border-radius:16px;padding:32px 36px;text-align:center;max-width:500px;margin:12vh auto 0 auto;
                        box-shadow:0 25px 50px -12px rgba(0,0,0,0.6);backdrop-filter:blur(16px);">
                <div style="font-size:2.2rem;margin-bottom:10px;">⚡</div>
                <div style="font-size:1.25rem;font-weight:700;color:#f8fafc;margin-bottom:6px;letter-spacing:-0.01em;">
                    Zenith AI Başlatılıyor
                </div>
                <div style="font-size:0.84rem;color:#94a3b8;margin-bottom:20px;line-height:1.5;">
                    Hibrit motor ve modeller ({CHAT_MODEL} & {EMBEDDING_MODEL}) hazırlanıyor...
                </div>
                <div style="height:4px;width:100%;background:rgba(255,255,255,0.08);border-radius:4px;overflow:hidden;margin-bottom:16px;">
                    <div style="height:100%;width:50%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:4px;animation:loadingBar 1.5s infinite ease-in-out;"></div>
                </div>
                <div style="display:inline-flex;align-items:center;gap:6px;font-size:0.75rem;color:#64748b;">
                    <span>🔒</span> Microsoft Foundry Local SDK • %100 Çevrimdışı Bellek
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    engine = get_rag_engine()
    st.session_state["models_loaded"] = True
    splash_slot.empty()

    # Aktif Oturum Yönetimi
    if "current_session_id" not in st.session_state:
        # Son aktif oturumu al veya yeni aç
        existing_sessions = engine.db.get_sessions()
        if existing_sessions:
            st.session_state.current_session_id = existing_sessions[0].session_id
        else:
            st.session_state.current_session_id = engine.db.create_session("İlk Doküman Analizi")

    # Mesajları Veritabanından Yükle
    saved_messages = engine.db.get_session_messages(st.session_state.current_session_id)
    messages_state = []
    for msg in saved_messages:
        sources_list = json.loads(msg.sources_json) if msg.sources_json else []
        messages_state.append({
            "role": msg.role,
            "content": msg.content,
            "sources": sources_list,
            "search_time": msg.search_time,
            "gen_time": msg.gen_time
        })

    # ── Sidebar: Sistem, Oturumlar ve Doküman Yönetimi ──
    with st.sidebar:
        st.markdown(
            """
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <div style="font-size:1.15rem;font-weight:700;color:#f8fafc;display:flex;align-items:center;gap:6px;">
                    <span>⚡</span> Zenith AI
                </div>
                <div class="status-badge">
                    <div class="status-dot"></div> Hibrit Aktif
                </div>
            </div>
            <div style="font-size:0.75rem;color:#94a3b8;margin-bottom:14px;">
                Dense Vector + SQLite FTS5 BM25 + RRF
            </div>
            """,
            unsafe_allow_html=True
        )

        # Yeni Sohbet Butonu
        if st.button("➕ Yeni Sohbet", use_container_width=True, type="primary"):
            new_id = engine.db.create_session(f"Analiz #{len(engine.db.get_sessions()) + 1}")
            st.session_state.current_session_id = new_id
            st.rerun()

        # Oturum Listesi
        all_sessions = engine.db.get_sessions()
        if len(all_sessions) > 1:
            st.markdown("<div style='font-size:0.75rem;font-weight:600;color:#94a3b8;margin:10px 0 6px 0;'>GEÇMİŞ ANALİZLER</div>", unsafe_allow_html=True)
            for sess in all_sessions[:5]:
                is_active = (sess.session_id == st.session_state.current_session_id)
                col_s1, col_s2 = st.columns([5, 1])
                with col_s1:
                    btn_label = f"💬 {sess.title}" if not is_active else f"👉 {sess.title}"
                    if st.button(btn_label, key=f"sess_{sess.session_id}", use_container_width=True):
                        st.session_state.current_session_id = sess.session_id
                        st.rerun()
                with col_s2:
                    if st.button("✕", key=f"del_sess_{sess.session_id}", help="Oturumu Sil"):
                        engine.db.delete_session(sess.session_id)
                        existing = engine.db.get_sessions()
                        st.session_state.current_session_id = existing[0].session_id if existing else engine.db.create_session()
                        st.rerun()

        st.divider()

        # Veritabanı İstatistikleri
        stats = engine.db.get_stats()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-value">{stats['total_chunks']}</div>
                    <div class="stat-label">Hibrit Öbek</div>
                </div>""",
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"""<div class="stat-card">
                    <div class="stat-value">{stats['total_files']}</div>
                    <div class="stat-label">Doküman</div>
                </div>""",
                unsafe_allow_html=True
            )

        st.markdown(
            f"""<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#64748b;margin:8px 2px 14px 2px;">
                <span>Vektör + BM25: <b>{stats['db_size_mb']} MB</b></span>
                <span>Boyut: <b>1024d</b></span>
            </div>""",
            unsafe_allow_html=True
        )

        # Doküman İşlemleri
        st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#cbd5e1;margin-bottom:8px;'>DOKÜMAN İŞLEMLERİ</div>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        if b1.button("🔄 İndeksle", use_container_width=True):
            with st.spinner("Dokümanlar işleniyor..."):
                res = engine.ingest_documents()
                if res["total_files"] == 0:
                    st.warning("⚠️ 'documents/' klasöründe geçerli doküman bulunamadı.")
                else:
                    st.toast(f"✅ {res['total_chunks']} hibrit öbek indekslendi!", icon="✅")
                    st.rerun()

        if b2.button("🗑️ Sıfırla", use_container_width=True):
            deleted = engine.db.clear_all()
            st.toast(f"Veritabanı sıfırlandı ({deleted} öbek silindi).", icon="🗑️")
            st.rerun()

        # Dosya Yükleme Dropzone
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Dokümanları yükleyin",
            type=[ext.replace(".", "") for ext in SUPPORTED_EXTENSIONS],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if uploaded_files:
            if "uploaded_file_names" not in st.session_state:
                st.session_state.uploaded_file_names = set()

            new_files = [u for u in uploaded_files if u.name not in st.session_state.uploaded_file_names]
            if new_files:
                os.makedirs(DOCUMENTS_DIR, exist_ok=True)
                saved = []
                for u_file in new_files:
                    save_path = os.path.join(DOCUMENTS_DIR, u_file.name)
                    try:
                        with open(save_path, "wb") as f:
                            f.write(u_file.getbuffer())
                        saved.append(u_file.name)
                    except Exception:
                        pass

                st.session_state.uploaded_file_names.update(saved)
                if saved:
                    st.toast(f"📥 {len(saved)} dosya kaydedildi.", icon="📥")
                    engine.ingest_documents()
                    st.rerun()

        st.divider()

        # İndekslenmiş Doküman Listesi
        st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#cbd5e1;margin-bottom:8px;'>AKTİF DOKÜMANLAR</div>", unsafe_allow_html=True)
        if stats["files"]:
            for f_info in stats["files"]:
                st.markdown(
                    f"""<div style="display:flex;justify-content:space-between;align-items:center;font-size:0.78rem;
                                color:#94a3b8;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.03);">
                        <span style="color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:170px;">
                            📄 {f_info['name']}
                        </span>
                        <span style="color:#64748b;font-size:0.72rem;">{f_info['chunks']} öbek</span>
                    </div>""",
                    unsafe_allow_html=True
                )
        else:
            st.caption("Henüz indekslenmiş doküman yok.")

        st.divider()

        # Sistem & Modeller
        st.markdown(
            f"""<div style="font-size:0.75rem;color:#64748b;line-height:1.6;">
                <div>🧠 <b>LLM:</b> {CHAT_MODEL}</div>
                <div>📐 <b>Vektör:</b> {EMBEDDING_MODEL}</div>
                <div>🔍 <b>Arama:</b> Hibrit (Dense + BM25)</div>
            </div>""",
            unsafe_allow_html=True
        )

        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

        if messages_state:
            chat_md = "# Zenith AI — Doküman Analiz Raporu\n\n"
            for m in messages_state:
                role_name = "Kullanıcı" if m["role"] == "user" else "Zenith AI"
                chat_md += f"### {role_name}\n{m['content']}\n\n"
                if m.get("sources"):
                    chat_md += "#### Doğrulanan Kaynaklar:\n"
                    for s in m["sources"]:
                        rel_pct = s.get("relevance", int(s.get("similarity", 0) * 100))
                        chat_md += f"- **[{s.get('citation_index', 1)}] {s['source_file']}** (Bölüm {s['chunk_index'] + 1}) — %{rel_pct} Alaka Düzeyi\n"
                    chat_md += "\n"
                chat_md += "---\n\n"

            st.download_button(
                label="📥 Raporu İndir (.md)",
                data=chat_md,
                file_name="zenith_ai_analiz_raporu.md",
                mime="text/markdown",
                use_container_width=True
            )

        if st.button("🔴 Oturumu Kapat", key="exit_btn", use_container_width=True):
            st.session_state["app_exited"] = True
            handle_exit_flow(engine)

    # ── Ana Sohbet ve İçerik Alanı ──
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">
                <span>⚡ Zenith AI</span>
                <span style="font-size:0.88rem;font-weight:500;color:#64748b;padding-left:8px;border-left:1px solid rgba(255,255,255,0.1);">
                    SOTA Hibrit RAG Asistanı
                </span>
            </div>
            <div class="hero-subtitle">
                Dense Vektör + BM25 FTS5 Hibrit Çıkarım Motoru • Cümle İçi Alıntılar • %100 Çevrimdışı Güvenlik
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Karşılama Kartları (Sohbet boşken)
    if not messages_state and engine.db.get_chunk_count() > 0:
        st.markdown("<div style='font-size:0.82rem;font-weight:600;color:#94a3b8;margin-bottom:10px;'>ÖRNEK ANALİZ SORGULARI</div>", unsafe_allow_html=True)
        sample_questions = [
            ("Mali Analiz", "Projenin bütçesi ve mali analizi nedir?"),
            ("Sorun & Çözüm", "En sık karşılaşılan sorunlar ve çözümleri nelerdir?"),
            ("Mimari & Özet", "Teknik altyapı ve kullanılan teknolojileri özetle."),
        ]
        q_cols = st.columns(3)
        for idx, (tag, q_text) in enumerate(sample_questions):
            with q_cols[idx]:
                if st.button(f"📌 **{tag}**\n\n{q_text}", key=f"sq_{idx}", use_container_width=True):
                    st.session_state.pending_question = q_text
                    st.rerun()

    # Geçmiş Mesajların Listelenmesi
    for idx, message in enumerate(messages_state):
        avatar = "🧑‍💻" if message["role"] == "user" else "⚡"
        with st.chat_message(message["role"], avatar=avatar):
            if message["role"] == "assistant":
                formatted_text = format_in_text_citations(message["content"])
                st.markdown(formatted_text, unsafe_allow_html=True)
                _render_action_bar(message["content"], f"hist_{idx}")

                if message.get("sources"):
                    with st.expander(f"📚 Doğrulanan Kaynaklar ({len(message['sources'])} Alıntı)"):
                        for src in message["sources"]:
                            rel_pct = src.get("relevance", int(src.get("similarity", 0) * 100))
                            cit_idx = src.get("citation_index", 1)
                            m_type = src.get("match_type", "hibrit")
                            st.markdown(
                                f"""<div class="source-item">
                                    <div class="source-header">
                                        <span class="source-name">
                                            <span class="citation-pill">[{cit_idx}]</span>
                                            📄 {src['source_file']} <span style="font-size:0.75rem;color:#64748b;">(Bölüm {src['chunk_index'] + 1})</span>
                                        </span>
                                        <span class="source-score">%{rel_pct} Alaka ({m_type.upper()})</span>
                                    </div>
                                    <div class="source-preview">{src.get('content', '')[:160]}...</div>
                                </div>""",
                                unsafe_allow_html=True
                            )

                if message.get("search_time") is not None and message.get("gen_time") is not None:
                    st.markdown(
                        f"""<div class="telemetry-pill">
                            ⏱️ Hibrit Arama: <b>{message['search_time']}s</b> &nbsp;•&nbsp; ⚡ Çıkarım: <b>{message['gen_time']}s</b>
                        </div>""",
                        unsafe_allow_html=True
                    )
            else:
                st.markdown(message["content"])

    # Sesli Soru Sorma Mikrofon Butonu
    _render_voice_mic_widget()

    # Kullanıcı Girdisi ve Soru-Cevap Akışı
    pending_prompt = st.session_state.pop("pending_question", None)
    user_input = st.chat_input("Dokümanlarınız hakkında bir soru sorun (veya mikrofonu kullanın)...")
    prompt = pending_prompt or user_input

    if prompt:
        if engine.db.get_chunk_count() == 0:
            st.warning("⚠️ Veritabanında indeksli doküman bulunmuyor. Lütfen önce sol menüden 'İndeksle' butonuna tıklayın.")
            st.stop()

        # Kullanıcı mesajını ekrana bas ve kaydet
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        engine.db.save_message(
            session_id=st.session_state.current_session_id,
            role="user",
            content=prompt
        )

        try:
            print(f"\n🔍 [Web UI] Soru: '{prompt}'")
        except Exception:
            pass

        with st.chat_message("assistant", avatar="⚡"):
            t_gen_start = time.time()
            with st.spinner("🔍 Hibrit Arama (Dense + FTS5 BM25) yapılıyor..."):
                sources, context, search_time = engine.query_search(prompt)

            try:
                print(f"📎 [Web UI] {len(sources)} kaynak bulundu (Arama: {search_time}s)")
            except Exception:
                pass

            answer_placeholder = st.empty()
            answer_placeholder.markdown("⚡ *Yanıt hazırlanıyor...*")

            # Çok turlu hafızayı motora ilet
            stream_gen = engine.query_generate(
                question=prompt,
                sources=sources,
                context=context,
                chat_history=messages_state
            )

            full_answer = ""
            for chunk in stream_gen:
                full_answer += chunk
                formatted_live = format_in_text_citations(full_answer)
                answer_placeholder.markdown(formatted_live + " ▌", unsafe_allow_html=True)

            formatted_final = format_in_text_citations(full_answer)
            answer_placeholder.markdown(formatted_final, unsafe_allow_html=True)
            _render_action_bar(full_answer, "live")
            gen_time = round(time.time() - t_gen_start, 2)

            try:
                print(f"⚡ [Web UI] Yanıt tamamlandı ({gen_time}s)\n")
            except Exception:
                pass

            sources_data = []
            if sources:
                sources_data = [
                    {
                        "source_file": s.source_file,
                        "chunk_index": s.chunk_index,
                        "similarity": s.similarity,
                        "relevance": s.relevance_percentage,
                        "citation_index": s.citation_index,
                        "match_type": s.match_type,
                        "content": s.content
                    }
                    for s in sources
                ]
                with st.expander(f"📚 Doğrulanan Kaynaklar ({len(sources_data)} Alıntı)"):
                    for src in sources_data:
                        st.markdown(
                            f"""<div class="source-item">
                                <div class="source-header">
                                    <span class="source-name">
                                        <span class="citation-pill">[{src['citation_index']}]</span>
                                        📄 {src['source_file']} <span style="font-size:0.75rem;color:#64748b;">(Bölüm {src['chunk_index'] + 1})</span>
                                    </span>
                                    <span class="source-score">%{src['relevance']} Alaka ({src['match_type'].upper()})</span>
                                </div>
                                <div class="source-preview">{src.get('content', '')[:160]}...</div>
                            </div>""",
                            unsafe_allow_html=True
                        )

            st.markdown(
                f"""<div class="telemetry-pill">
                    ⏱️ Hibrit Arama: <b>{search_time}s</b> &nbsp;•&nbsp; ⚡ Çıkarım: <b>{gen_time}s</b>
                </div>""",
                unsafe_allow_html=True
            )

        # Asistan yanıtını veritabanına kaydet
        engine.db.save_message(
            session_id=st.session_state.current_session_id,
            role="assistant",
            content=full_answer,
            sources=sources_data,
            search_time=search_time,
            gen_time=gen_time
        )
        st.rerun()


if __name__ == "__main__":
    main()
