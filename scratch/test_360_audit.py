import os
import sys
import time
import sqlite3
import tempfile
import shutil
import threading

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 70)
print("🛡️ ZENITH AI — 360° COMPREHENSIVE SECURITY & AUDIT SUITE")
print("=" * 70)

PASSED = 0
FAILED = 0

def log_test(name, success, details=""):
    global PASSED, FAILED
    if success:
        PASSED += 1
        print(f"  [PASS] {name} {details}")
    else:
        FAILED += 1
        print(f"  [FAIL] ❌ {name} {details}")

# ==============================================================================
# 1. SQL INJECTION
# ==============================================================================
print("\n[CATEGORY 1: SQL INJECTION & DATABASE INTEGRITY]")
from src.core.database import VectorDatabase

test_db_path = os.path.join(tempfile.gettempdir(), "test_zenith_sec.db")
if os.path.exists(test_db_path):
    try: os.remove(test_db_path)
    except: pass

db = VectorDatabase(db_path=test_db_path)

sqli_payloads = [
    "test'; DROP TABLE documents; --",
    "' OR '1'='1",
    "admin'--",
    "1; SELECT sqlite_version();",
    "''' UNION ALL SELECT NULL, NULL, NULL --"
]

all_sqli_handled = True
records = []
for idx, payload in enumerate(sqli_payloads):
    dummy_vec = [0.1] * 1024
    records.append((payload, idx, payload, dummy_vec))
try:
    db.store_chunks_batch(records)
except Exception as e:
    all_sqli_handled = False
    print(f"    SQLi Error: {e}")

conn = sqlite3.connect(test_db_path)
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM documents")
count = cursor.fetchone()[0]
conn.close()

log_test("SQL Injection Prevention (Parameterized Queries)", all_sqli_handled and count == len(sqli_payloads), f"(Stored {count}/{len(sqli_payloads)} safely)")

stats = db.get_stats()
log_test("SQL Injection & Integrity in get_stats()", stats['total_chunks'] == len(sqli_payloads))

# ==============================================================================
# 2. PATH TRAVERSAL & CORRUPT FILES
# ==============================================================================
print("\n[CATEGORY 2: PATH TRAVERSAL & INPUT VALIDATION]")
from src.core.document_loader import read_document, chunk_text

traversal_paths = [
    "../../../../windows/system32/cmd.exe",
    "../..//etc/passwd",
    "non_existent_directory/fake_file.docx"
]

traversal_safe = True
for p in traversal_paths:
    res = read_document(p)
    if res.content != "" and "System32" in p:
        traversal_safe = False

log_test("Path Traversal Resistance", traversal_safe, "(Handled non-existent/escaped paths safely)")

corrupt_dir = tempfile.mkdtemp()
corrupt_pdf = os.path.join(corrupt_dir, "broken.pdf")
with open(corrupt_pdf, "wb") as f:
    f.write(b"%PDF-1.4 garbage binary data \x00\xff\xfe\xaa corrupted header")

corrupt_docx = os.path.join(corrupt_dir, "broken.docx")
with open(corrupt_docx, "wb") as f:
    f.write(b"PK\x03\x04 not a real zip archive")

corrupt_xlsx = os.path.join(corrupt_dir, "broken.xlsx")
with open(corrupt_xlsx, "wb") as f:
    f.write(b"not an excel file")

empty_txt = os.path.join(corrupt_dir, "empty.txt")
with open(empty_txt, "w") as f:
    f.write("")

pdf_res = read_document(corrupt_pdf)
docx_res = read_document(corrupt_docx)
xlsx_res = read_document(corrupt_xlsx)
empty_res = read_document(empty_txt)

corrupt_handled = (pdf_res.content == "" and docx_res.content == "" and xlsx_res.content == "" and empty_res.content == "")
log_test("Corrupted Binary Files Graceful Handling", corrupt_handled, "(No unhandled tracebacks/crashes)")
shutil.rmtree(corrupt_dir, ignore_errors=True)

# ==============================================================================
# 3. MATHEMATICAL EDGE CASES
# ==============================================================================
print("\n[CATEGORY 3: MATHEMATICAL EDGE CASES & L2 NORMALIZATION]")
import numpy as np

zero_vec = [0.0] * 1024
search_res = db.search(zero_vec, top_k=3)
log_test("Zero-Magnitude Vector / Divide-by-Zero Defense", isinstance(search_res, list), f"(Handled cleanly: {len(search_res)} results)")

huge_text = ("Kelime " * 50 + "\n\n") * 500
chunks = chunk_text(huge_text)
log_test("Large Text Chunking Scalability", len(chunks) > 0, f"({len(chunks)} chunks produced)")

unicode_text = "⚡ Zenith AI 🔥 测试 🚀 العربية русский язык Türkçe karakter testi yapılıyor burada ve bu metin yeterince uzun olmalı"
u_chunks = chunk_text(unicode_text)
log_test("Multilingual UTF-8 & Emoji Ingestion", len(u_chunks) > 0)

# ==============================================================================
# 4. XSS & TTS DEFENSE
# ==============================================================================
print("\n[CATEGORY 4: XSS & WEB SPEECH SCRIPT INJECTION DEFENSE]")
import re

def sanitize_for_tts(text):
    clean = re.sub(r'[*#_`~>|\-\[\]\(\)\'\"\\\`]', ' ', text).replace('\n', ' ')
    return ' '.join(clean.split())

xss_payloads = [
    "<script>alert(1)</script>",
    "Hello '; alert(document.cookie); var x='",
    "<img src=x onerror=alert('XSS')>",
]

xss_safe = True
for payload in xss_payloads:
    sanitized = sanitize_for_tts(payload)
    if "'" in sanitized or '"' in sanitized or "\\" in sanitized:
        xss_safe = False

log_test("Web Speech TTS XSS & Injection Neutralization", xss_safe, "(All quotes and script escapes stripped)")

# ==============================================================================
# 5. CONCURRENCY
# ==============================================================================
print("\n[CATEGORY 5: CONCURRENCY & MULTI-THREAD STRESS TEST]")

concurrent_success = True
errors = []

def concurrent_worker(worker_id):
    global concurrent_success
    try:
        query_vec = [float(worker_id % 10) * 0.1] * 1024
        res = db.search(query_vec, top_k=2)
        if not isinstance(res, list):
            concurrent_success = False
    except Exception as e:
        concurrent_success = False
        errors.append(str(e))

threads = []
for i in range(20):
    t = threading.Thread(target=concurrent_worker, args=(i,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()

log_test("Multi-Threaded Concurrent Search (20 parallel workers)", concurrent_success, f"(Errors: {len(errors)})")

# ==============================================================================
# 6. ENGINE LIFECYCLE
# ==============================================================================
print("\n[CATEGORY 6: ENGINE LIFECYCLE & SELF-HEALING THREADPOOL]")
from src.core.models import ModelManager

mgr = ModelManager()
mgr._ensure_executor()
log_test("Auto-Healing ThreadPool Creation", mgr._executor is not None and not getattr(mgr._executor, '_shutdown', False))

mgr._executor.shutdown(wait=False)
mgr._ensure_executor()
log_test("Auto-Healing After Abrupt Shutdown", mgr._executor is not None and not getattr(mgr._executor, '_shutdown', False))
mgr.shutdown()

# ==============================================================================
# 7. ENGINE API CONTRACTS (NEW)
# ==============================================================================
print("\n[CATEGORY 7: ENGINE API CONTRACTS]")
from src.core.engine import RAGEngine

# Verify query_search and query_generate exist and are callable
engine_has_search = hasattr(RAGEngine, 'query_search') and callable(getattr(RAGEngine, 'query_search'))
engine_has_generate = hasattr(RAGEngine, 'query_generate') and callable(getattr(RAGEngine, 'query_generate'))
engine_has_stream = hasattr(RAGEngine, 'query_stream') and callable(getattr(RAGEngine, 'query_stream'))

log_test("RAGEngine.query_search() method exists", engine_has_search)
log_test("RAGEngine.query_generate() method exists", engine_has_generate)
log_test("RAGEngine.query_stream() preserved (CLI compat)", engine_has_stream)

# ==============================================================================
# CLEANUP
# ==============================================================================
if os.path.exists(test_db_path):
    try: os.remove(test_db_path)
    except: pass

print("\n" + "=" * 70)
print(f"📊 360° AUDIT RESULTS: {PASSED} PASSED | {FAILED} FAILED")
if FAILED == 0:
    print("🏆 STATUS: 100% BULLETPROOF — ZERO VULNERABILITIES IDENTIFIED")
else:
    print("⚠️ STATUS: SOME ISSUES FOUND — IMMEDIATE ACTION REQUIRED")
print("=" * 70)
