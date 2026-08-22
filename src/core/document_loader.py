"""
Belge İşleme ve Metin Çıkarma Modülü (src/core/document_loader.py)
===================================================================
PDF, DOCX, XLSX, PPTX, TXT ve MD dosyalarından metin ayıklar ve öbekler (chunking).
"""

import os
from typing import List
from src.config import DOCUMENTS_DIR, SUPPORTED_EXTENSIONS, CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_LENGTH
from src.core.models import TextChunk, DocumentInfo

# Opsiyonel belge okuyucu kütüphaneleri
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import pptx
except ImportError:
    pptx = None


def scan_documents(directory: str = DOCUMENTS_DIR) -> List[str]:
    """Dizindeki desteklenen uzantıya sahip tüm belgeleri tarar ve yollarını döndürür."""
    if not os.path.isdir(directory):
        print(f"⚠️  Belge dizini bulunamadı: {directory}")
        return []

    found_files: List[str] = []
    for root, _dirs, files in os.walk(directory):
        for file_name in sorted(files):
            ext = os.path.splitext(file_name)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                found_files.append(os.path.join(root, file_name))
    return found_files


def _extract_pdf(file_path: str) -> str:
    """PDF dosyasından metin çıkarır."""
    if pypdf is None:
        print("⚠️  PDF okunamadı: pypdf kütüphanesi yüklü değil.")
        return ""
    try:
        reader = pypdf.PdfReader(file_path)
        text_parts = [page.extract_text().strip() for page in reader.pages if page.extract_text()]
        return "\n\n".join(text_parts)
    except Exception as e:
        print(f"⚠️  PDF okuma hatası ({file_path}): {e}")
        return ""


def _extract_docx(file_path: str) -> str:
    """Word (.docx) dosyasından metin ve tablo verilerini çıkarır."""
    if docx is None:
        print("⚠️  DOCX okunamadı: python-docx kütüphanesi yüklü değil.")
        return ""
    try:
        doc = docx.Document(file_path)
        parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n\n".join(parts)
    except Exception as e:
        print(f"⚠️  DOCX okuma hatası ({file_path}): {e}")
        return ""


def _extract_xlsx(file_path: str) -> str:
    """Excel (.xlsx) dosyasındaki tüm sayfaları ve satırları okur."""
    if openpyxl is None:
        print("⚠️  XLSX okunamadı: openpyxl kütüphanesi yüklü değil.")
        return ""
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        parts = []
        for name in wb.sheetnames:
            parts.append(f"=== Sayfa: {name} ===")
            for row in wb[name].iter_rows(values_only=True):
                vals = [str(v).strip() for v in row if v is not None]
                if vals:
                    parts.append(" | ".join(vals))
        wb.close()
        return "\n".join(parts)
    except Exception as e:
        print(f"⚠️  XLSX okuma hatası ({file_path}): {e}")
        return ""


def _extract_pptx(file_path: str) -> str:
    """PowerPoint (.pptx) sunumundaki slayt metinlerini çıkarır."""
    if pptx is None:
        print("⚠️  PPTX okunamadı: python-pptx kütüphanesi yüklü değil.")
        return ""
    try:
        prs = pptx.Presentation(file_path)
        parts = []
        for i, slide in enumerate(prs.slides):
            parts.append(f"=== Slayt {i+1} ===")
            slide_txt = [shape.text.strip() for shape in slide.shapes if hasattr(shape, "text") and shape.text.strip()]
            if slide_txt:
                parts.append("\n".join(slide_txt))
        return "\n\n".join(parts)
    except Exception as e:
        print(f"⚠️  PPTX okuma hatası ({file_path}): {e}")
        return ""


def read_document(file_path: str) -> DocumentInfo:
    """Dosya uzantısına göre uygun okuyucuyu çağırır ve metni döndürür."""
    file_name = os.path.basename(file_path)
    ext = os.path.splitext(file_name)[1].lower()

    if ext in (".md", ".txt"):
        content = ""
        for enc in ["utf-8", "utf-8-sig", "cp1254", "latin-1"]:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
    elif ext == ".pdf":
        content = _extract_pdf(file_path)
    elif ext == ".docx":
        content = _extract_docx(file_path)
    elif ext == ".xlsx":
        content = _extract_xlsx(file_path)
    elif ext == ".pptx":
        content = _extract_pptx(file_path)
    else:
        raise ValueError(f"Desteklenmeyen uzantı: {ext}")

    return DocumentInfo(file_path=file_path, file_name=file_name, content=content)


def chunk_text(text: str) -> List[str]:
    """Metni kayan pencere (sliding window) algoritmasıyla küçük öbeklere böler."""
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in text.strip().split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for p in paragraphs:
        if len(p) > CHUNK_SIZE:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(p):
                end = start + CHUNK_SIZE
                split = p.rfind(" ", start, end) if end < len(p) else len(p)
                if split <= start:
                    split = end
                chunks.append(p[start:split])
                start = max(0, split - CHUNK_OVERLAP) if split < len(p) else len(p)
            continue

        test = f"{current}\n\n{p}" if current else p
        if len(test) <= CHUNK_SIZE:
            current = test
        else:
            if current:
                chunks.append(current)
            current = p

    if current:
        chunks.append(current)

    return [c.strip() for c in chunks if len(c.strip()) >= MIN_CHUNK_LENGTH]


def process_document(file_path: str) -> DocumentInfo:
    """Tek bir belgeyi okur ve metin öbeklerini (chunks) oluşturur."""
    doc = read_document(file_path)
    if not doc.content or not doc.content.strip():
        doc.chunks = []
        return doc
    raw_chunks = chunk_text(doc.content)
    doc.chunks = [
        TextChunk(content=c, source_file=doc.file_name, chunk_index=i)
        for i, c in enumerate(raw_chunks)
    ]
    return doc


def process_all_documents(directory: str = DOCUMENTS_DIR) -> List[DocumentInfo]:
    """Taranan tüm belgeleri okur ve öbeklerine ayırır."""
    paths = scan_documents(directory)
    docs = []
    for p in paths:
        try:
            d = process_document(p)
            docs.append(d)
            print(f"  ✅ {d.file_name} → {len(d.chunks)} chunk")
        except Exception as e:
            print(f"  ❌ {os.path.basename(p)} → Hata: {e}")
    return docs
