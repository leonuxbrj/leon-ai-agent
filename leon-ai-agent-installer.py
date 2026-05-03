"""
Leon AI Agent - Instalador Automático
Execute este script no Windows para instalar e rodar o agente.
Ele cria todos os arquivos necessários automaticamente.
"""

import os
import sys
import json
import subprocess
import urllib.request

def create_project(base_dir):
    """Create all project files."""
    print("🧠 Leon AI Agent - Instalador")
    print("=" * 40)

    project_dir = os.path.join(base_dir, "leon-ai-agent")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "watched_files"), exist_ok=True)

    # requirements.txt
    write_file(project_dir, "requirements.txt", """google-generativeai>=0.8.0
requests>=2.31.0
beautifulsoup4>=4.12.0
Pillow>=10.0.0
chardet>=5.2.0
PyPDF2>=3.0.0
python-docx>=1.1.0
watchdog>=4.0.0
""")

    # config.json
    write_file(project_dir, "config.json", json.dumps({
        "api_key": "AIzaSyC7VY48pRubbIcD0G-UvVSLhSD_wWCLM2g",
        "model": "gemini-2.0-flash",
        "agent_name": "Leon AI Agent",
        "max_output_tokens": 8192,
        "temperature": 0.7,
        "restrictions": [
            "Responda sempre em português brasileiro",
            "Seja direto e prático",
            "Não execute comandos destrutivos sem confirmação explícita",
            "Mantenha um log de todas as ações realizadas"
        ],
        "allowed_commands": [
            "dir", "ls", "cd", "mkdir", "copy", "move", "del", "type", "cat",
            "echo", "find", "grep", "ping", "ipconfig", "systeminfo",
            "python", "pip", "node", "npm", "git", "curl", "wget"
        ],
        "blocked_commands": [
            "format", "fdisk", "rm -rf /", "rmdir /s /q C:\\",
            "reg delete", "net user", "net localgroup",
            "taskkill /f /im", "shutdown"
        ],
        "watch_folder": "watched_files",
        "memory_db": "memory.db",
        "log_file": "agent.log",
        "theme": "dark",
        "language": "pt-BR"
    }, indent=2, ensure_ascii=False))

    # memory.py
    write_file(project_dir, "memory.py", MEMORY_CODE)

    # ai_engine.py
    write_file(project_dir, "ai_engine.py", AI_ENGINE_CODE)

    # file_processor.py
    write_file(project_dir, "file_processor.py", FILE_PROCESSOR_CODE)

    # task_executor.py
    write_file(project_dir, "task_executor.py", TASK_EXECUTOR_CODE)

    # main.py
    write_file(project_dir, "main.py", MAIN_CODE)

    # build.py
    write_file(project_dir, "build.py", BUILD_CODE)

    return project_dir

def write_file(directory, filename, content):
    filepath = os.path.join(directory, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {filename}")

def install_and_run(project_dir):
    """Install dependencies and run the app."""
    print("\n📦 Instalando dependências...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-r",
        os.path.join(project_dir, "requirements.txt")
    ])

    print("\n🚀 Iniciando Leon AI Agent...")
    os.chdir(project_dir)
    subprocess.run([sys.executable, "main.py"])

# === ALL MODULE CODE ===

MEMORY_CODE = r'''import sqlite3
import json
import os
from datetime import datetime

class Memory:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL, timestamp TEXT NOT NULL, metadata TEXT);
            CREATE TABLE IF NOT EXISTS knowledge (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, content TEXT NOT NULL, category TEXT DEFAULT 'general', timestamp TEXT NOT NULL, metadata TEXT);
            CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, filepath TEXT NOT NULL, file_type TEXT, summary TEXT, content_preview TEXT, timestamp TEXT NOT NULL, metadata TEXT);
            CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, action_type TEXT NOT NULL, description TEXT NOT NULL, result TEXT, timestamp TEXT NOT NULL, metadata TEXT);
        """)
        self.conn.commit()

    def add_message(self, role, content, metadata=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO conversations (role, content, timestamp, metadata) VALUES (?,?,?,?)", (role, content, datetime.now().isoformat(), json.dumps(metadata) if metadata else None))
        self.conn.commit()
        return c.lastrowid

    def get_recent_messages(self, limit=50):
        c = self.conn.cursor()
        c.execute("SELECT role, content, timestamp FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
        return list(reversed(c.fetchall()))

    def add_knowledge(self, source, content, category="general", metadata=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO knowledge (source, content, category, timestamp, metadata) VALUES (?,?,?,?,?)", (source, content, category, datetime.now().isoformat(), json.dumps(metadata) if metadata else None))
        self.conn.commit()
        return c.lastrowid

    def search_knowledge(self, query, limit=10):
        c = self.conn.cursor()
        c.execute("SELECT source, content, category FROM knowledge WHERE content LIKE ? ORDER BY id DESC LIMIT ?", (f"%{query}%", limit))
        return c.fetchall()

    def add_file(self, filename, filepath, file_type=None, summary=None, content_preview=None, metadata=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO files (filename, filepath, file_type, summary, content_preview, timestamp, metadata) VALUES (?,?,?,?,?,?,?)", (filename, filepath, file_type, summary, content_preview, datetime.now().isoformat(), json.dumps(metadata) if metadata else None))
        self.conn.commit()
        return c.lastrowid

    def search_files(self, query, limit=10):
        c = self.conn.cursor()
        c.execute("SELECT filename, filepath, file_type, summary FROM files WHERE filename LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT ?", (f"%{query}%", f"%{query}%", limit))
        return c.fetchall()

    def log_action(self, action_type, description, result=None, metadata=None):
        c = self.conn.cursor()
        c.execute("INSERT INTO actions (action_type, description, result, timestamp, metadata) VALUES (?,?,?,?,?)", (action_type, description, result, datetime.now().isoformat(), json.dumps(metadata) if metadata else None))
        self.conn.commit()
        return c.lastrowid

    def get_recent_actions(self, limit=20):
        c = self.conn.cursor()
        c.execute("SELECT action_type, description, result, timestamp FROM actions ORDER BY id DESC LIMIT ?", (limit,))
        return list(reversed(c.fetchall()))

    def get_stats(self):
        c = self.conn.cursor()
        stats = {}
        for t in ["conversations", "knowledge", "files", "actions"]:
            c.execute(f"SELECT COUNT(*) FROM {t}")
            stats[t] = c.fetchone()[0]
        return stats

    def close(self):
        self.conn.close()
'''

AI_ENGINE_CODE = r'''import google.generativeai as genai
from datetime import datetime
import json

class GeminiAI:
    def __init__(self, api_key, model="gemini-2.0-flash", temperature=0.7, max_tokens=8192):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = genai.GenerativeModel(model_name=model, generation_config=genai.types.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens))
        self.chat = None
        self.system_instruction = ""
        self.restrictions = []

    def set_system_instruction(self, instruction):
        self.system_instruction = instruction

    def set_restrictions(self, restrictions):
        self.restrictions = restrictions

    def _build_system_prompt(self):
        parts = []
        if self.system_instruction: parts.append(self.system_instruction)
        if self.restrictions:
            parts.append("\n=== RESTRIÇÕES DO USUÁRIO ===")
            for i, r in enumerate(self.restrictions, 1): parts.append(f"{i}. {r}")
            parts.append("=== FIM DAS RESTRIÇÕES ===")
        parts.append(f"\nData e hora atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        return "\n".join(parts)

    def start_chat(self, history=None):
        system_prompt = self._build_system_prompt()
        if history:
            formatted = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in history]
            self.chat = self.model.start_chat(history=formatted)
        else:
            self.chat = self.model.start_chat()
        if system_prompt:
            try: self.chat.send_message(f"[SYSTEM]\n{system_prompt}")
            except: pass

    def send_message(self, message, context=None):
        if not self.chat: self.start_chat()
        full = f"[CONTEXTO]\n{context}\n\n[FIM]\n\n{message}" if context else message
        try:
            r = self.chat.send_message(full)
            return {"success": True, "text": r.text, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}

    def generate_once(self, prompt, context=None):
        sp = self._build_system_prompt()
        fp = f"{sp}\n\n{f'[CONTEXTO] {context} [/CONTEXTO]' if context else ''}\n\n{prompt}"
        try:
            r = self.model.generate_content(fp)
            return {"success": True, "text": r.text, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}

    def analyze_file_content(self, content, filename, instruction=None):
        p = f"Analise o arquivo '{filename}' e forneça: 1) Resumo 2) Pontos-chave 3) Possíveis usos\n{f'Instrução: {instruction}' if instruction else ''}\n\nConteúdo:\n{content[:15000]}"
        return self.generate_once(p)

    def plan_task(self, task, tools=None):
        ti = "\nFerramentas:\n" + "\n".join(f"- {t}" for t in tools) if tools else ""
        return self.generate_once(f"Crie um plano para: {task}\n{ti}\nForneça passos, comandos, problemas possíveis e resultado esperado.")

    def reset_chat(self): self.chat = None
    def get_model_info(self): return {"model": self.model_name, "temperature": self.temperature, "max_tokens": self.max_tokens}
'''

FILE_PROCESSOR_CODE = r'''import os
import chardet
from datetime import datetime
from pathlib import Path

class FileProcessor:
    SUPPORTED_TEXT = {'.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.csv', '.log', '.ini', '.cfg', '.conf', '.sh', '.bat', '.ps1', '.sql', '.r', '.rb', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.cs', '.php', '.toml', '.env'}

    def __init__(self, watch_folder="watched_files"):
        self.watch_folder = watch_folder
        os.makedirs(watch_folder, exist_ok=True)

    def read_file(self, filepath):
        filepath = os.path.abspath(filepath)
        if not os.path.exists(filepath):
            return {"success": False, "error": f"Arquivo não encontrado: {filepath}"}
        ext = Path(filepath).suffix.lower()
        try:
            if ext == '.pdf': return self._read_pdf(filepath)
            elif ext in {'.docx', '.doc'}: return self._read_docx(filepath)
            else: return self._read_text(filepath)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _read_text(self, filepath):
        with open(filepath, 'rb') as f: raw = f.read()
        enc = chardet.detect(raw).get('encoding', 'utf-8') or 'utf-8'
        try: content = raw.decode(enc)
        except: content = raw.decode('utf-8', errors='replace')
        return {"success": True, "content": content, "encoding": enc, "size": len(raw), "type": "text"}

    def _read_pdf(self, filepath):
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
        return {"success": True, "content": text, "pages": len(reader.pages), "type": "pdf"}

    def _read_docx(self, filepath):
        from docx import Document
        doc = Document(filepath)
        text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return {"success": True, "content": text, "type": "docx"}

    def list_files(self, folder=None):
        target = folder or self.watch_folder
        if not os.path.exists(target): return []
        files = []
        for root, dirs, fnames in os.walk(target):
            for fname in fnames:
                fp = os.path.join(root, fname)
                s = os.stat(fp)
                files.append({"name": fname, "path": fp, "size": s.st_size, "modified": datetime.fromtimestamp(s.st_mtime).isoformat(), "extension": Path(fname).suffix.lower()})
        return files

    def search_in_files(self, query, folder=None):
        target = folder or self.watch_folder
        results = []
        if not os.path.exists(target): return results
        for root, dirs, fnames in os.walk(target):
            for fname in fnames:
                try:
                    r = self.read_file(os.path.join(root, fname))
                    if r["success"] and query.lower() in r["content"].lower():
                        matches = [{"line_num": i, "text": l.strip()[:200]} for i, l in enumerate(r["content"].split('\n'), 1) if query.lower() in l.lower()]
                        results.append({"file": fname, "path": os.path.join(root, fname), "matches": matches[:5], "total_matches": len(matches)})
                except: continue
        return results
'''

TASK_EXECUTOR_CODE = r'''import subprocess
import os
import re
import requests
from datetime import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

class TaskExecutor:
    def __init__(self, allowed_commands=None, blocked_commands=None, working_dir=None):
        self.allowed_commands = allowed_commands or []
        self.blocked_commands = blocked_commands or []
        self.working_dir = working_dir or os.getcwd()
        self.action_log = []

    def _is_command_allowed(self, command):
        cmd = command.lower().strip()
        for b in self.blocked_commands:
            if b.lower() in cmd: return False, f"Bloqueado: '{b}'"
        if not self.allowed_commands: return True, ""
        base = cmd.split()[0] if cmd.split() else ""
        for a in self.allowed_commands:
            if base == a.lower() or base.startswith(a.lower()): return True, ""
        return False, f"'{base}' não permitido"

    def execute_command(self, command, timeout=30):
        ok, reason = self._is_command_allowed(command)
        if not ok: return {"success": False, "error": reason}
        try:
            r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, cwd=self.working_dir)
            self.action_log.append({"type": "cmd", "desc": command, "ts": datetime.now().isoformat()})
            return {"success": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode}
        except subprocess.TimeoutExpired: return {"success": False, "error": f"Timeout {timeout}s"}
        except Exception as e: return {"success": False, "error": str(e)}

    def web_search(self, query, num_results=5):
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            results = []
            for res in soup.select('.result'):
                t = res.select_one('.result__title a')
                s = res.select_one('.result__snippet')
                if t:
                    link = t.get('href', '')
                    if 'uddg=' in link: link = link.split('uddg=')[1].split('&')[0]
                    results.append({"title": t.get_text(strip=True), "url": link, "snippet": s.get_text(strip=True) if s else ""})
                if len(results) >= num_results: break
            return {"success": True, "results": results}
        except Exception as e: return {"success": False, "error": str(e)}

    def fetch_webpage(self, url, max_chars=10000):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'footer']): tag.decompose()
            text = re.sub(r'\n{3,}', '\n\n', soup.get_text('\n', strip=True))
            return {"success": True, "title": soup.title.string if soup.title else "", "content": text[:max_chars]}
        except Exception as e: return {"success": False, "error": str(e)}

    def list_directory(self, path=None):
        t = path or self.working_dir
        try:
            items = [{"name": i, "type": "dir" if os.path.isdir(os.path.join(t, i)) else "file"} for i in os.listdir(t)]
            return {"success": True, "path": t, "items": items}
        except Exception as e: return {"success": False, "error": str(e)}

    def get_system_info(self):
        import platform
        return {"system": platform.system(), "node": platform.node(), "release": platform.release(), "cwd": self.working_dir}
'''

MAIN_CODE = r'''import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import json, os, sys, threading, shutil, subprocess
from datetime import datetime
from pathlib import Path
from ai_engine import GeminiAI
from memory import Memory
from file_processor import FileProcessor
from task_executor import TaskExecutor

class LeonAIAgent:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self._load_config()
        self.memory = Memory(os.path.join(self.base_dir, self.config.get("memory_db", "memory.db")))
        self.file_processor = FileProcessor(os.path.join(self.base_dir, self.config.get("watch_folder", "watched_files")))
        self.task_executor = TaskExecutor(allowed_commands=self.config.get("allowed_commands", []), blocked_commands=self.config.get("blocked_commands", []), working_dir=self.base_dir)
        self.ai = GeminiAI(api_key=self.config["api_key"], model=self.config.get("model", "gemini-2.0-flash"), temperature=self.config.get("temperature", 0.7), max_tokens=self.config.get("max_output_tokens", 8192))
        self.ai.set_restrictions(self.config.get("restrictions", []))
        self.root = tk.Tk()
        self.root.title(self.config.get("agent_name", "Leon AI Agent"))
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        self._setup_theme()
        self._build_gui()
        self._load_history()
        self.ai.start_chat()

    def _load_config(self):
        p = os.path.join(self.base_dir, "config.json")
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f: return json.load(f)
        return {"api_key": "", "model": "gemini-2.0-flash", "agent_name": "Leon AI Agent", "restrictions": [], "allowed_commands": [], "blocked_commands": []}

    def _save_config(self):
        with open(os.path.join(self.base_dir, "config.json"), 'w', encoding='utf-8') as f: json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _setup_theme(self):
        self.c = {"bg": "#1a1a2e", "bg2": "#16213e", "input": "#0f3460", "accent": "#e94560", "hover": "#ff6b6b", "text": "#eee", "dim": "#a0a0b0", "ok": "#4ecca3", "err": "#e94560", "border": "#2d4059"}
        self.root.configure(bg=self.c["bg"])

    def _build_gui(self):
        main = tk.Frame(self.root, bg=self.c["bg"])
        main.pack(fill=tk.BOTH, expand=True)
        sb = tk.Frame(main, bg=self.c["bg2"], width=220)
        sb.pack(side=tk.LEFT, fill=tk.Y); sb.pack_propagate(False)
        tf = tk.Frame(sb, bg=self.c["bg2"]); tf.pack(fill=tk.X, pady=(15,20), padx=10)
        tk.Label(tf, text="🧠", font=("Segoe UI Emoji",28), bg=self.c["bg2"], fg=self.c["accent"]).pack()
        tk.Label(tf, text="Leon AI Agent", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack()
        for txt, cmd in [("💬  Chat",self._s_chat),("📁  Arquivos",self._s_files),("🔍  Buscar",self._s_search),("⚙️  Restrições",self._s_restrict),("📊  Memória",self._s_memory),("🌐  Navegar",self._s_web),("🖥️  Terminal",self._s_term)]:
            b = tk.Button(sb, text=txt, font=("Segoe UI",11), bg=self.c["bg2"], fg=self.c["text"], activebackground=self.c["input"], relief=tk.FLAT, anchor="w", padx=20, pady=10, cursor="hand2", command=cmd)
            b.pack(fill=tk.X, padx=5, pady=2)
            b.bind("<Enter>", lambda e,b=b: b.configure(bg=self.c["input"]))
            b.bind("<Leave>", lambda e,b=b: b.configure(bg=self.c["bg2"]))
        self.stats_lbl = tk.Label(sb, text="", font=("Segoe UI",8), bg=self.c["bg2"], fg=self.c["dim"], justify=tk.LEFT)
        self.stats_lbl.pack(side=tk.BOTTOM, anchor="w", padx=10, pady=10)
        self.cf = tk.Frame(main, bg=self.c["bg"]); self.cf.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self._build_chat(); self._build_files(); self._build_search(); self._build_restrict(); self._build_memory(); self._build_web(); self._build_term()
        self._s_chat(); self._upd_stats()

    def _build_chat(self):
        self.v_chat = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_chat, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="💬 Chat com IA", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        cc = tk.Frame(self.v_chat, bg=self.c["bg"]); cc.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.chat_disp = scrolledtext.ScrolledText(cc, wrap=tk.WORD, font=("Segoe UI",11), bg=self.c["bg"], fg=self.c["text"], relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.chat_disp.pack(fill=tk.BOTH, expand=True)
        for t,f,fo in [("user_name",self.c["accent"],("Segoe UI",10,"bold")),("ai_name",self.c["ok"],("Segoe UI",10,"bold")),("system",self.c["dim"],("Segoe UI",9,"italic")),("user_msg",self.c["text"],("Segoe UI",11)),("ai_msg",self.c["text"],("Segoe UI",11)),("error_msg",self.c["err"],("Segoe UI",11))]:
            self.chat_disp.tag_configure(t, foreground=f, font=fo)
        inf = tk.Frame(self.v_chat, bg=self.c["bg2"], height=80); inf.pack(fill=tk.X, padx=10, pady=(0,10)); inf.pack_propagate(False)
        br = tk.Frame(inf, bg=self.c["bg2"]); br.pack(fill=tk.X, padx=10, pady=(8,0))
        for txt, cmd in [("📎 Anexar", self._attach),("🗑️ Limpar", self._clear_chat),("🔄 Nova", self._new_conv)]:
            tk.Button(br, text=txt, font=("Segoe UI",9), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, padx=10, pady=3, cursor="hand2", command=cmd).pack(side=tk.LEFT, padx=2)
        ir = tk.Frame(inf, bg=self.c["bg2"]); ir.pack(fill=tk.X, padx=10, pady=(5,8))
        self.chat_in = tk.Text(ir, font=("Segoe UI",11), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, height=2, padx=10, pady=8, wrap=tk.WORD)
        self.chat_in.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_in.bind("<Return>", self._on_enter)
        tk.Button(ir, text="Enviar ➤", font=("Segoe UI",11,"bold"), bg=self.c["accent"], fg="white", relief=tk.FLAT, padx=15, pady=8, cursor="hand2", command=self._send).pack(side=tk.RIGHT, padx=(8,0))

    def _build_files(self):
        self.v_files = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_files, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="📁 Arquivos Monitorados", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        bf = tk.Frame(h, bg=self.c["bg2"]); bf.pack(side=tk.RIGHT, padx=15)
        for txt, cmd in [("📂 Pasta", self._open_folder),("📥 Adicionar", self._add_file),("🔄 Atualizar", self._refresh_files)]:
            tk.Button(bf, text=txt, font=("Segoe UI",9), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, padx=10, pady=3, cursor="hand2", command=cmd).pack(side=tk.LEFT, padx=2)
        self.files_disp = scrolledtext.ScrolledText(self.v_files, wrap=tk.WORD, font=("Consolas",10), bg=self.c["bg2"], fg=self.c["text"], relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.files_disp.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_search(self):
        self.v_search = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_search, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="🔍 Buscar Conhecimento", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        sf = tk.Frame(self.v_search, bg=self.c["bg"]); sf.pack(fill=tk.X, padx=10, pady=10)
        self.search_in = tk.Entry(sf, font=("Segoe UI",12), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT)
        self.search_in.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,5))
        self.search_in.bind("<Return>", lambda e: self._do_search())
        tk.Button(sf, text="Buscar", font=("Segoe UI",11,"bold"), bg=self.c["accent"], fg="white", relief=tk.FLAT, padx=15, pady=6, cursor="hand2", command=self._do_search).pack(side=tk.RIGHT)
        self.search_disp = scrolledtext.ScrolledText(self.v_search, wrap=tk.WORD, font=("Segoe UI",11), bg=self.c["bg"], fg=self.c["text"], relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.search_disp.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

    def _build_restrict(self):
        self.v_restrict = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_restrict, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="⚙️ Restrições", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        self.restrict_ed = scrolledtext.ScrolledText(self.v_restrict, wrap=tk.WORD, font=("Segoe UI",11), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, padx=15, pady=10)
        self.restrict_ed.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.restrict_ed.insert(tk.END, "\n".join(self.config.get("restrictions", [])))
        bf = tk.Frame(self.v_restrict, bg=self.c["bg"]); bf.pack(fill=tk.X, padx=10, pady=(0,10))
        tk.Button(bf, text="💾 Salvar", font=("Segoe UI",11,"bold"), bg=self.c["ok"], fg="white", relief=tk.FLAT, padx=15, pady=6, cursor="hand2", command=self._save_restrict).pack(side=tk.LEFT)
        tk.Button(bf, text="➕ Comando Permitido", font=("Segoe UI",10), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, padx=10, pady=4, cursor="hand2", command=self._add_cmd).pack(side=tk.LEFT, padx=5)

    def _build_memory(self):
        self.v_memory = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_memory, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="📊 Memória", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        tk.Button(h, text="🔄 Atualizar", font=("Segoe UI",9), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, padx=10, pady=3, cursor="hand2", command=self._refresh_mem).pack(side=tk.RIGHT, padx=15)
        self.mem_disp = scrolledtext.ScrolledText(self.v_memory, wrap=tk.WORD, font=("Consolas",10), bg=self.c["bg"], fg=self.c["text"], relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.mem_disp.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_web(self):
        self.v_web = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_web, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="🌐 Navegação Web", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        wf = tk.Frame(self.v_web, bg=self.c["bg"]); wf.pack(fill=tk.X, padx=10, pady=10)
        self.web_in = tk.Entry(wf, font=("Segoe UI",12), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT)
        self.web_in.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,5))
        self.web_in.insert(0, "URL ou busca...")
        self.web_in.bind("<FocusIn>", lambda e: self.web_in.delete(0,tk.END) if self.web_in.get().startswith("URL") else None)
        tk.Button(wf, text="🔍 Buscar", font=("Segoe UI",10), bg=self.c["accent"], fg="white", relief=tk.FLAT, padx=10, pady=5, cursor="hand2", command=lambda: self._do_web("search")).pack(side=tk.LEFT, padx=2)
        tk.Button(wf, text="🌐 Abrir", font=("Segoe UI",10), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT, padx=10, pady=5, cursor="hand2", command=lambda: self._do_web("fetch")).pack(side=tk.LEFT, padx=2)
        self.web_disp = scrolledtext.ScrolledText(self.v_web, wrap=tk.WORD, font=("Segoe UI",11), bg=self.c["bg"], fg=self.c["text"], relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.web_disp.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

    def _build_term(self):
        self.v_term = tk.Frame(self.cf, bg=self.c["bg"])
        h = tk.Frame(self.v_term, bg=self.c["bg2"], height=50); h.pack(fill=tk.X); h.pack_propagate(False)
        tk.Label(h, text="🖥️ Terminal", font=("Segoe UI",14,"bold"), bg=self.c["bg2"], fg=self.c["text"]).pack(side=tk.LEFT, padx=15, pady=10)
        tk.Label(h, text=f"CWD: {self.task_executor.working_dir}", font=("Consolas",9), bg=self.c["bg2"], fg=self.c["dim"]).pack(side=tk.RIGHT, padx=15)
        cf = tk.Frame(self.v_term, bg=self.c["bg"]); cf.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(cf, text="$", font=("Consolas",14,"bold"), bg=self.c["bg"], fg=self.c["accent"]).pack(side=tk.LEFT, padx=(0,5))
        self.cmd_in = tk.Entry(cf, font=("Consolas",12), bg=self.c["input"], fg=self.c["text"], relief=tk.FLAT)
        self.cmd_in.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0,5))
        self.cmd_in.bind("<Return>", lambda e: self._exec_cmd())
        tk.Button(cf, text="Executar ▶", font=("Segoe UI",10,"bold"), bg=self.c["accent"], fg="white", relief=tk.FLAT, padx=12, pady=5, cursor="hand2", command=self._exec_cmd).pack(side=tk.RIGHT)
        self.term_disp = scrolledtext.ScrolledText(self.v_term, wrap=tk.WORD, font=("Consolas",10), bg="#0d1117", fg="#58a6ff", relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.term_disp.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        for t,f in [("cmd","#58a6ff"),("stdout","#c9d1d9"),("stderr","#f85149"),("ok","#3fb950"),("err","#f85149")]:
            self.term_disp.tag_configure(t, foreground=f)

    def _hide_all(self):
        for v in [self.v_chat, self.v_files, self.v_search, self.v_restrict, self.v_memory, self.v_web, self.v_term]: v.pack_forget()
    def _show(self, v): self._hide_all(); v.pack(fill=tk.BOTH, expand=True)
    def _s_chat(self): self._show(self.v_chat)
    def _s_files(self): self._show(self.v_files); self._refresh_files()
    def _s_search(self): self._show(self.v_search)
    def _s_restrict(self): self._show(self.v_restrict)
    def _s_memory(self): self._show(self.v_memory); self._refresh_mem()
    def _s_web(self): self._show(self.v_web)
    def _s_term(self): self._show(self.v_term)

    def _append(self, who, msg, tag="ai"):
        self.chat_disp.configure(state=tk.NORMAL)
        self.chat_disp.insert(tk.END, f"\n{'━'*50}\n", "system")
        self.chat_disp.insert(tk.END, f" {who}\n", f"{tag}_name")
        self.chat_disp.insert(tk.END, f"{msg}\n\n", f"{tag}_msg")
        self.chat_disp.configure(state=tk.DISABLED); self.chat_disp.see(tk.END)

    def _sys(self, msg):
        self.chat_disp.configure(state=tk.NORMAL)
        self.chat_disp.insert(tk.END, f"  ⚙ {msg}\n", "system")
        self.chat_disp.configure(state=tk.DISABLED); self.chat_disp.see(tk.END)

    def _send(self):
        txt = self.chat_in.get("1.0", tk.END).strip()
        if not txt: return
        self.chat_in.delete("1.0", tk.END)
        self._append("Você", txt, "user")
        self.memory.add_message("user", txt)
        if txt.startswith("/"): self._handle_cmd(txt); return
        threading.Thread(target=self._process, args=(txt,), daemon=True).start()

    def _process(self, txt):
        self.root.after(0, lambda: self._sys("Pensando..."))
        ctx = self._build_ctx(txt)
        r = self.ai.send_message(txt, context=ctx)
        if r["success"]:
            self.memory.add_message("assistant", r["text"])
            self.root.after(0, lambda: self._append("🧠 Kai", r["text"], "ai"))
        else:
            self.root.after(0, lambda: self._append("❌ Erro", r.get("error","Erro"), "error"))
        self.root.after(0, self._upd_stats)

    def _build_ctx(self, txt):
        parts = []
        kn = self.memory.search_knowledge(txt, limit=3)
        if kn:
            parts.append("=== CONHECIMENTO ===")
            for k in kn: parts.append(f"[{k['source']}] {k['content'][:500]}")
            parts.append("=== FIM ===\n")
        return "\n".join(parts) if parts else None

    def _handle_cmd(self, txt):
        parts = txt.split(maxsplit=1)
        cmd, arg = parts[0].lower(), parts[1] if len(parts)>1 else ""
        if cmd == "/clear": self._clear_chat()
        elif cmd == "/reset": self.ai.reset_chat(); self.ai.start_chat(); self._sys("Reiniciado.")
        elif cmd == "/files": self._s_files()
        elif cmd == "/search": self.search_in.delete(0,tk.END); self.search_in.insert(0,arg); self._s_search(); self._do_search()
        elif cmd == "/exec": self._s_term(); self.cmd_in.delete(0,tk.END); self.cmd_in.insert(0,arg); self._exec_cmd()
        elif cmd == "/help": self._sys("Comandos: /clear /reset /files /search /exec /help")
        else: self._sys(f"Desconhecido: {cmd}")

    def _on_enter(self, e):
        if not e.state & 0x1: self._send(); return "break"

    def _attach(self):
        fp = filedialog.askopenfilename(title="Selecionar arquivo")
        if fp: threading.Thread(target=self._do_attach, args=(fp,), daemon=True).start()

    def _do_attach(self, fp):
        self.root.after(0, lambda: self._sys(f"Processando: {os.path.basename(fp)}..."))
        r = self.file_processor.read_file(fp)
        if r["success"]:
            fn = os.path.basename(fp)
            self.memory.add_file(fn, fp, r.get("type"), content_preview=r["content"][:1000])
            a = self.ai.analyze_file_content(r["content"], fn)
            if a["success"]: self.memory.add_knowledge(fn, r["content"][:5000], "file")
            self.root.after(0, lambda: self._append("📎 Arquivo", f"**{fn}** analisado.\n\n{a.get('text','') if a['success'] else a.get('error','')}", "system"))
        else:
            self.root.after(0, lambda: self._append("❌ Erro", r["error"], "error"))
        self.root.after(0, self._upd_stats)

    def _clear_chat(self):
        self.chat_disp.configure(state=tk.NORMAL); self.chat_disp.delete("1.0",tk.END); self.chat_disp.configure(state=tk.DISABLED)
    def _new_conv(self):
        self._clear_chat(); self.ai.reset_chat(); self.ai.start_chat(); self._sys("Nova conversa.")
    def _load_history(self):
        msgs = self.memory.get_recent_messages(limit=10)
        if msgs:
            self._sys(f"Histórico: {len(msgs)} mensagens carregadas.")
            for m in msgs[-5:]:
                if m['role']=='user': self._append("Você", m['content'], "user")
                else: self._append("🧠 Kai", m['content'], "ai")

    def _refresh_files(self):
        files = self.file_processor.list_files()
        self.files_disp.configure(state=tk.NORMAL); self.files_disp.delete("1.0",tk.END)
        if not files:
            self.files_disp.insert(tk.END, f"Nenhum arquivo.\nPasta: {self.file_processor.watch_folder}\nUse '📥 Adicionar' para começar.")
        else:
            self.files_disp.insert(tk.END, f"📁 {len(files)} arquivo(s)\nPasta: {self.file_processor.watch_folder}\n\n")
            for f in files:
                s = f['size']; ss = f"{s/1048576:.1f}MB" if s>1048576 else f"{s/1024:.1f}KB" if s>1024 else f"{s}B"
                self.files_disp.insert(tk.END, f"  📄 {f['name']}  ({ss})  {f['extension']}\n     {f['modified']}\n\n")
        self.files_disp.configure(state=tk.DISABLED)

    def _open_folder(self):
        p = os.path.abspath(self.file_processor.watch_folder); os.makedirs(p, exist_ok=True)
        if sys.platform=='win32': os.startfile(p)
        elif sys.platform=='darwin': subprocess.run(['open',p])
        else: subprocess.run(['xdg-open',p])

    def _add_file(self):
        fp = filedialog.askopenfilename(title="Adicionar arquivo")
        if fp: shutil.copy2(fp, os.path.join(self.file_processor.watch_folder, os.path.basename(fp))); self._refresh_files()

    def _do_search(self):
        q = self.search_in.get().strip()
        if not q: return
        self.search_disp.configure(state=tk.NORMAL); self.search_disp.delete("1.0",tk.END)
        self.search_disp.insert(tk.END, f"🔍 '{q}'...\n\n")
        kn = self.memory.search_knowledge(q)
        if kn:
            self.search_disp.insert(tk.END, f"📚 Conhecimento ({len(kn)}):\n\n")
            for k in kn: self.search_disp.insert(tk.END, f"  [{k['category']}] {k['source']}\n  {k['content'][:300]}...\n\n")
        fr = self.file_processor.search_in_files(q)
        if fr:
            self.search_disp.insert(tk.END, f"📁 Arquivos ({len(fr)}):\n\n")
            for r in fr:
                self.search_disp.insert(tk.END, f"  📄 {r['file']} ({r['total_matches']})\n")
                for m in r['matches'][:3]: self.search_disp.insert(tk.END, f"    L{m['line_num']}: {m['text'][:100]}\n")
                self.search_disp.insert(tk.END, "\n")
        if not kn and not fr: self.search_disp.insert(tk.END, "Nenhum resultado.")
        self.search_disp.configure(state=tk.DISABLED)

    def _save_restrict(self):
        txt = self.restrict_ed.get("1.0",tk.END).strip()
        r = [l.strip() for l in txt.split("\n") if l.strip()]
        self.config["restrictions"] = r; self.ai.set_restrictions(r); self._save_config()
        messagebox.showinfo("OK", f"{len(r)} restrições salvas!")

    def _add_cmd(self):
        c = simpledialog.askstring("Comando", "Nome do comando permitido:")
        if c:
            self.config.setdefault("allowed_commands",[]).append(c.strip())
            self.task_executor.allowed_commands = self.config["allowed_commands"]; self._save_config()

    def _refresh_mem(self):
        s = self.memory.get_stats()
        self.mem_disp.configure(state=tk.NORMAL); self.mem_disp.delete("1.0",tk.END)
        self.mem_disp.insert(tk.END, "📊 MEMÓRIA\n" + "═"*40 + "\n\n")
        self.mem_disp.insert(tk.END, f"  💬 Conversas: {s['conversations']}\n  📚 Conhecimento: {s['knowledge']}\n  📁 Arquivos: {s['files']}\n  ⚡ Ações: {s['actions']}\n\n")
        aa = self.memory.get_recent_actions(10)
        if aa:
            self.mem_disp.insert(tk.END, "⚡ AÇÕES RECENTES\n" + "═"*40 + "\n\n")
            for a in aa: self.mem_disp.insert(tk.END, f"  [{a['timestamp'][:16]}] {a['action_type']}: {a['description'][:80]}\n")
        self.mem_disp.configure(state=tk.DISABLED)

    def _do_web(self, t):
        q = self.web_in.get().strip()
        if not q or q.startswith("URL"): return
        self.web_disp.configure(state=tk.NORMAL); self.web_disp.delete("1.0",tk.END)
        self.web_disp.insert(tk.END, f"Processando: {q}\n"); self.web_disp.configure(state=tk.DISABLED)
        threading.Thread(target=self._web_thread, args=(q,t), daemon=True).start()

    def _web_thread(self, q, t):
        if t=="search": r = self.task_executor.web_search(q); self.root.after(0, lambda: self._show_web_search(r, q))
        else: r = self.task_executor.fetch_webpage(q); self.root.after(0, lambda: self._show_web_fetch(r, q))

    def _show_web_search(self, r, q):
        self.web_disp.configure(state=tk.NORMAL); self.web_disp.delete("1.0",tk.END)
        if r["success"]:
            self.web_disp.insert(tk.END, f"🔍 '{q}'\n\n")
            for i,x in enumerate(r["results"],1): self.web_disp.insert(tk.END, f"{i}. {x['title']}\n   {x['url']}\n   {x['snippet']}\n\n")
            self.memory.add_knowledge("web", json.dumps(r["results"], ensure_ascii=False), "web")
        else: self.web_disp.insert(tk.END, f"❌ {r['error']}")
        self.web_disp.configure(state=tk.DISABLED)

    def _show_web_fetch(self, r, q):
        self.web_disp.configure(state=tk.NORMAL); self.web_disp.delete("1.0",tk.END)
        if r["success"]:
            self.web_disp.insert(tk.END, f"🌐 {r['title']}\nURL: {q}\n\n{'═'*50}\n\n{r['content']}")
            self.memory.add_knowledge(q, r["content"][:5000], "webpage")
        else: self.web_disp.insert(tk.END, f"❌ {r['error']}")
        self.web_disp.configure(state=tk.DISABLED)

    def _exec_cmd(self):
        cmd = self.cmd_in.get().strip()
        if not cmd: return
        self.cmd_in.delete(0,tk.END)
        self.term_disp.configure(state=tk.NORMAL)
        self.term_disp.insert(tk.END, f"$ {cmd}\n", "cmd")
        r = self.task_executor.execute_command(cmd)
        if r["success"]:
            if r.get("stdout"): self.term_disp.insert(tk.END, r["stdout"], "stdout")
            if r.get("stderr"): self.term_disp.insert(tk.END, r["stderr"], "stderr")
            self.term_disp.insert(tk.END, "✓ OK\n\n", "ok")
        else: self.term_disp.insert(tk.END, f"✗ {r['error']}\n\n", "err")
        self.term_disp.configure(state=tk.DISABLED); self.term_disp.see(tk.END)

    def _upd_stats(self):
        s = self.memory.get_stats()
        self.stats_lbl.configure(text=f"💬 {s['conversations']} msgs\n📚 {s['knowledge']} conhec.\n📁 {s['files']} arquivos\n⚡ {s['actions']} ações")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", lambda: (self.memory.close(), self.root.destroy()))
        self.root.mainloop()

if __name__ == "__main__":
    os.makedirs("watched_files", exist_ok=True)
    LeonAIAgent().run()
'''

BUILD_CODE = r'''import subprocess, sys, os
def main():
    print("📦 Instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("🔨 Gerando .exe...")
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "--name=LeonAIAgent", "--add-data=config.json;.", "--hidden-import=google.generativeai", "--hidden-import=chardet", "--hidden-import=PyPDF2", "--hidden-import=docx", "--hidden-import=bs4", "--hidden-import=requests", "--noconfirm", "main.py"])
    print("\n✅ dist/LeonAIAgent.exe pronto!")
if __name__ == "__main__": main()
'''

if __name__ == "__main__":
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    project = create_project(desktop)
    print(f"\n✅ Projeto criado em: {project}")
    resp = input("\nInstalar dependências e executar agora? (s/n): ").strip().lower()
    if resp in ('s', 'sim', 'y', 'yes'):
        install_and_run(project)
    else:
        print(f"\nPara rodar manualmente:")
        print(f"  cd {project}")
        print(f"  pip install -r requirements.txt")
        print(f"  python main.py")
        input("\nPressione Enter para sair...")
