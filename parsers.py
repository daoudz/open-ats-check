"""
parsers.py - Multi-format file-to-text extraction module.
Supports PDF, DOCX, TXT, RTF, and HTML files.
"""

import os
import re
from io import BytesIO


def extract_text(file_storage, filename=None):
    """
    Extract plain text from an uploaded file.
    
    Args:
        file_storage: A Flask FileStorage object or file-like object (BytesIO).
        filename: Optional filename override (used when file_storage has no filename).
        
    Returns:
        dict with keys:
            - text: extracted plain text
            - format: detected file format
            - metadata: dict with structural info (headings found, etc.)
    """
    if filename is None:
        filename = getattr(file_storage, 'filename', 'unknown.txt')

    ext = os.path.splitext(filename)[1].lower()
    
    parsers = {
        '.pdf': _parse_pdf,
        '.docx': _parse_docx,
        '.doc': _parse_docx,
        '.txt': _parse_txt,
        '.rtf': _parse_rtf,
        '.html': _parse_html,
        '.htm': _parse_html,
    }

    parser = parsers.get(ext)
    if parser is None:
        raise ValueError(f"Unsupported file format: {ext}. Supported: {', '.join(parsers.keys())}")

    # Ensure stream is at the beginning (critical for Flask FileStorage objects)
    if hasattr(file_storage, 'seek'):
        file_storage.seek(0)
    elif hasattr(file_storage, 'stream'):
        file_storage.stream.seek(0)

    raw_bytes = file_storage.read()
    text = parser(raw_bytes)
    text = _clean_text(text)
    metadata = _extract_structure(text)

    return {
        'text': text,
        'format': ext.lstrip('.'),
        'metadata': metadata,
    }


def _parse_pdf(raw_bytes):
    """Extract text from PDF bytes."""
    from PyPDF2 import PdfReader
    reader = PdfReader(BytesIO(raw_bytes))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)
    return '\n'.join(pages)


def _parse_docx(raw_bytes):
    """Extract text from DOCX bytes."""
    from docx import Document
    doc = Document(BytesIO(raw_bytes))
    paragraphs = [p.text for p in doc.paragraphs]
    return '\n'.join(paragraphs)


def _parse_txt(raw_bytes):
    """Extract text from plain text bytes."""
    for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            continue
    return raw_bytes.decode('utf-8', errors='replace')


def _parse_rtf(raw_bytes):
    """Extract text from RTF bytes."""
    from striprtf.striprtf import rtf_to_text
    rtf_content = raw_bytes.decode('utf-8', errors='replace')
    return rtf_to_text(rtf_content)


def _parse_html(raw_bytes):
    """Extract text from HTML bytes."""
    from bs4 import BeautifulSoup
    html_content = raw_bytes.decode('utf-8', errors='replace')
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for tag in soup(['script', 'style', 'meta', 'link']):
        tag.decompose()
    return soup.get_text(separator='\n')


def _clean_text(text):
    """Clean extracted text: normalize whitespace, remove excessive blank lines."""
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def _extract_structure(text):
    """
    Extract structural metadata from the text.
    Returns info about detected headings, sections, etc.
    """
    lines = text.split('\n')
    
    standard_headings = [
        'work experience', 'experience', 'professional experience', 'employment history',
        'education', 'academic background', 'qualifications',
        'skills', 'technical skills', 'core competencies', 'competencies',
        'certifications', 'certificates', 'licenses',
        'summary', 'professional summary', 'objective', 'career objective', 'profile',
        'projects', 'portfolio',
        'awards', 'honors', 'achievements',
        'references', 'volunteer', 'volunteering', 'languages',
        'publications', 'interests', 'hobbies',
        'contact', 'contact information', 'personal information',
    ]
    
    found_headings = []
    for i, line in enumerate(lines):
        stripped = line.strip().lower().rstrip(':')
        if stripped in standard_headings:
            found_headings.append({
                'text': line.strip(),
                'line': i + 1,
                'standard': True,
            })
        elif len(stripped) > 0 and len(stripped) < 40 and stripped == stripped.upper() and not stripped.isdigit():
            # Potential all-caps heading
            found_headings.append({
                'text': line.strip(),
                'line': i + 1,
                'standard': stripped.lower().rstrip(':') in standard_headings,
            })

    return {
        'total_lines': len(lines),
        'total_chars': len(text),
        'headings_found': found_headings,
        'has_standard_sections': any(h['standard'] for h in found_headings),
    }
