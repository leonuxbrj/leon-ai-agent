"""
File processor - handles reading, analyzing, and managing files.
"""

import os
import json
import chardet
from datetime import datetime
from pathlib import Path


class FileProcessor:
    SUPPORTED_TEXT = {'.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
                     '.yaml', '.yml', '.csv', '.log', '.ini', '.cfg', '.conf', '.sh',
                     '.bat', '.ps1', '.sql', '.r', '.rb', '.go', '.rs', '.java', '.c',
                     '.cpp', '.h', '.hpp', '.cs', '.php', '.swift', '.kt', '.scala',
                     '.toml', '.env', '.gitignore', '.dockerfile', '.makefile'}

    SUPPORTED_DOCS = {'.pdf', '.docx', '.doc'}
    SUPPORTED_DATA = {'.csv', '.json', '.xml', '.yaml', '.yml'}

    def __init__(self, watch_folder="watched_files"):
        self.watch_folder = watch_folder
        os.makedirs(watch_folder, exist_ok=True)

    def read_file(self, filepath):
        """Read and return file content with encoding detection."""
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            return {"success": False, "error": f"Arquivo não encontrado: {filepath}"}

        ext = Path(filepath).suffix.lower()

        try:
            if ext in self.SUPPORTED_TEXT or ext in self.SUPPORTED_DATA:
                return self._read_text_file(filepath)
            elif ext == '.pdf':
                return self._read_pdf(filepath)
            elif ext in {'.docx', '.doc'}:
                return self._read_docx(filepath)
            else:
                return self._read_text_file(filepath)
        except Exception as e:
            return {"success": False, "error": f"Erro ao ler arquivo: {str(e)}"}

    def _read_text_file(self, filepath):
        """Read text file with encoding detection."""
        with open(filepath, 'rb') as f:
            raw = f.read()

        detected = chardet.detect(raw)
        encoding = detected.get('encoding', 'utf-8') or 'utf-8'

        try:
            content = raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            content = raw.decode('utf-8', errors='replace')

        return {
            "success": True,
            "content": content,
            "encoding": encoding,
            "size": len(raw),
            "type": "text"
        }

    def _read_pdf(self, filepath):
        """Read PDF file."""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(filepath)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            content = "\n\n".join(text_parts)
            return {
                "success": True,
                "content": content,
                "pages": len(reader.pages),
                "type": "pdf"
            }
        except ImportError:
            return {"success": False, "error": "PyPDF2 não instalado. Execute: pip install PyPDF2"}

    def _read_docx(self, filepath):
        """Read DOCX file."""
        try:
            from docx import Document
            doc = Document(filepath)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            content = "\n\n".join(paragraphs)
            return {
                "success": True,
                "content": content,
                "paragraphs": len(paragraphs),
                "type": "docx"
            }
        except ImportError:
            return {"success": False, "error": "python-docx não instalado. Execute: pip install python-docx"}

    def list_files(self, folder=None):
        """List all files in the watch folder."""
        target = folder or self.watch_folder
        if not os.path.exists(target):
            return []

        files = []
        for root, dirs, filenames in os.walk(target):
            for fname in filenames:
                fpath = os.path.join(root, fname)
                stat = os.stat(fpath)
                files.append({
                    "name": fname,
                    "path": fpath,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "extension": Path(fname).suffix.lower()
                })
        return files

    def save_to_watch_folder(self, filename, content):
        """Save content to the watch folder."""
        filepath = os.path.join(self.watch_folder, filename)
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def get_file_summary(self, filepath):
        """Get a quick summary of a file."""
        result = self.read_file(filepath)
        if not result["success"]:
            return result

        content = result["content"]
        lines = content.split('\n')

        return {
            "success": True,
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "type": result.get("type", "unknown"),
            "total_lines": len(lines),
            "total_chars": len(content),
            "preview": content[:500] + ("..." if len(content) > 500 else ""),
            "extension": Path(filepath).suffix.lower()
        }

    def search_in_files(self, query, folder=None):
        """Search for text across all files in folder."""
        target = folder or self.watch_folder
        results = []
        if not os.path.exists(target):
            return results

        for root, dirs, filenames in os.walk(target):
            for fname in filenames:
                fpath = os.path.join(root, fname)
                try:
                    result = self.read_file(fpath)
                    if result["success"] and query.lower() in result["content"].lower():
                        # Find matching lines
                        matches = []
                        for i, line in enumerate(result["content"].split('\n'), 1):
                            if query.lower() in line.lower():
                                matches.append({"line_num": i, "text": line.strip()[:200]})

                        results.append({
                            "file": fname,
                            "path": fpath,
                            "matches": matches[:5],
                            "total_matches": len(matches)
                        })
                except Exception:
                    continue

        return results
