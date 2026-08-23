"""
Zenith AI — Başlatıcı Giriş Noktası (app.py)
==============================================
Uygulamayı başlatan kök giriş modülü. `src.ui.cli` ve `src.ui.web` bileşenlerini çağırır.
"""

import os
import sys
import io

# Windows konsolunda UTF-8 desteği (emoji çökme koruması)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Proje kök dizinini sys.path'e otomatik ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ui.cli import run_cli

if __name__ == "__main__":
    run_cli()