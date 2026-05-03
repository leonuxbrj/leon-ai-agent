"""
Leon AI Agent - Main GUI Application
A local AI agent powered by Gemini with file processing, task execution, and persistent memory.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

# Local modules
from ai_engine import GeminiAI
from memory import Memory
from file_processor import FileProcessor
from task_executor import TaskExecutor


class LeonAIAgent:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self._load_config()

        # Initialize components
        self.memory = Memory(os.path.join(self.base_dir, self.config.get("memory_db", "memory.db")))
        self.file_processor = FileProcessor(os.path.join(self.base_dir, self.config.get("watch_folder", "watched_files")))
        self.task_executor = TaskExecutor(
            allowed_commands=self.config.get("allowed_commands", []),
            blocked_commands=self.config.get("blocked_commands", []),
            working_dir=self.base_dir
        )
        self.ai = GeminiAI(
            api_key=self.config["api_key"],
            model=self.config.get("model", "gemini-2.0-flash"),
            temperature=self.config.get("temperature", 0.7),
            max_tokens=self.config.get("max_output_tokens", 8192)
        )
        self.ai.set_restrictions(self.config.get("restrictions", []))

        # Build GUI
        self.root = tk.Tk()
        self.root.title(self.config.get("agent_name", "Leon AI Agent"))
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        self._setup_theme()
        self._build_gui()
        self._load_history_to_chat()

        # Start chat session
        self.ai.start_chat()

    def _load_config(self):
        config_path = os.path.join(self.base_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "api_key": "",
            "model": "gemini-2.0-flash",
            "agent_name": "Leon AI Agent",
            "restrictions": [],
            "allowed_commands": [],
            "blocked_commands": []
        }

    def _save_config(self):
        config_path = os.path.join(self.base_dir, "config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def _setup_theme(self):
        self.colors = {
            "bg": "#1a1a2e",
            "bg_secondary": "#16213e",
            "bg_input": "#0f3460",
            "accent": "#e94560",
            "accent_hover": "#ff6b6b",
            "text": "#eee",
            "text_secondary": "#a0a0b0",
            "user_msg": "#533483",
            "ai_msg": "#0f3460",
            "system_msg": "#2d4059",
            "success": "#4ecca3",
            "error": "#e94560",
            "border": "#2d4059"
        }
        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TFrame", background=self.colors["bg"])
        style.configure("Dark.TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("Dark.TButton", background=self.colors["accent"], foreground=self.colors["text"])
        style.configure("Sidebar.TFrame", background=self.colors["bg_secondary"])
        style.configure("Sidebar.TButton", background=self.colors["bg_secondary"],
                        foreground=self.colors["text"], padding=10)

    def _build_gui(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors["bg"])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(main_container, bg=self.colors["bg_secondary"], width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Logo / Title
        title_frame = tk.Frame(sidebar, bg=self.colors["bg_secondary"])
        title_frame.pack(fill=tk.X, pady=(15, 20), padx=10)
        tk.Label(title_frame, text="🧠", font=("Segoe UI Emoji", 28),
                 bg=self.colors["bg_secondary"], fg=self.colors["accent"]).pack()
        tk.Label(title_frame, text="Leon AI Agent", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack()
        tk.Label(title_frame, text="Gemini Powered", font=("Segoe UI", 9),
                 bg=self.colors["bg_secondary"], fg=self.colors["text_secondary"]).pack()

        # Sidebar buttons
        btn_config = [
            ("💬  Chat", self._show_chat),
            ("📁  Arquivos", self._show_files),
            ("🔍  Buscar", self._show_search),
            ("⚙️  Restrições", self._show_restrictions),
            ("📊  Memória", self._show_memory),
            ("🌐  Navegar", self._show_web),
            ("🖥️  Terminal", self._show_terminal),
        ]

        self.sidebar_buttons = []
        for text, command in btn_config:
            btn = tk.Button(sidebar, text=text, font=("Segoe UI", 11),
                           bg=self.colors["bg_secondary"], fg=self.colors["text"],
                           activebackground=self.colors["bg_input"],
                           activeforeground=self.colors["text"],
                           relief=tk.FLAT, anchor="w", padx=20, pady=10,
                           cursor="hand2", command=command)
            btn.pack(fill=tk.X, padx=5, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.colors["bg_input"]))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.colors["bg_secondary"]))
            self.sidebar_buttons.append(btn)

        # Stats at bottom of sidebar
        stats_frame = tk.Frame(sidebar, bg=self.colors["bg_secondary"])
        stats_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        self.stats_label = tk.Label(stats_frame, text="", font=("Segoe UI", 8),
                                    bg=self.colors["bg_secondary"], fg=self.colors["text_secondary"],
                                    justify=tk.LEFT)
        self.stats_label.pack(anchor="w")
        self._update_stats()

        # Content area
        self.content_frame = tk.Frame(main_container, bg=self.colors["bg"])
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Build all views (chat is default)
        self._build_chat_view()
        self._build_files_view()
        self._build_search_view()
        self._build_restrictions_view()
        self._build_memory_view()
        self._build_web_view()
        self._build_terminal_view()

        # Show chat by default
        self._show_chat()

    def _build_chat_view(self):
        self.chat_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        # Chat header
        header = tk.Frame(self.chat_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="💬 Chat com IA", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        # Model info
        model_info = self.ai.get_model_info()
        tk.Label(header, text=f"Modelo: {model_info['model']}", font=("Segoe UI", 9),
                 bg=self.colors["bg_secondary"], fg=self.colors["text_secondary"]).pack(side=tk.RIGHT, padx=15)

        # Chat display
        chat_container = tk.Frame(self.chat_view, bg=self.colors["bg"])
        chat_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_display = scrolledtext.ScrolledText(
            chat_container, wrap=tk.WORD, font=("Segoe UI", 11),
            bg=self.colors["bg"], fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT, padx=15, pady=10,
            state=tk.DISABLED,
            selectbackground=self.colors["accent"]
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Configure message tags
        self.chat_display.tag_configure("user_name", foreground=self.colors["accent"],
                                        font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("ai_name", foreground=self.colors["success"],
                                        font=("Segoe UI", 10, "bold"))
        self.chat_display.tag_configure("system", foreground=self.colors["text_secondary"],
                                        font=("Segoe UI", 9, "italic"))
        self.chat_display.tag_configure("user_msg", foreground=self.colors["text"],
                                        font=("Segoe UI", 11), lmargin1=20, lmargin2=20)
        self.chat_display.tag_configure("ai_msg", foreground=self.colors["text"],
                                        font=("Segoe UI", 11), lmargin1=20, lmargin2=20)
        self.chat_display.tag_configure("error_msg", foreground=self.colors["error"],
                                        font=("Segoe UI", 11))
        self.chat_display.tag_configure("separator", foreground=self.colors["border"])

        # Input area
        input_frame = tk.Frame(self.chat_view, bg=self.colors["bg_secondary"], height=80)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        input_frame.pack_propagate(False)

        # Buttons row
        btn_row = tk.Frame(input_frame, bg=self.colors["bg_secondary"])
        btn_row.pack(fill=tk.X, padx=10, pady=(8, 0))

        btn_attach = tk.Button(btn_row, text="📎 Anexar Arquivo", font=("Segoe UI", 9),
                               bg=self.colors["bg_input"], fg=self.colors["text"],
                               relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                               command=self._attach_file)
        btn_attach.pack(side=tk.LEFT, padx=(0, 5))

        btn_clear = tk.Button(btn_row, text="🗑️ Limpar Chat", font=("Segoe UI", 9),
                              bg=self.colors["bg_input"], fg=self.colors["text"],
                              relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                              command=self._clear_chat)
        btn_clear.pack(side=tk.LEFT, padx=(0, 5))

        btn_new_chat = tk.Button(btn_row, text="🔄 Nova Conversa", font=("Segoe UI", 9),
                                 bg=self.colors["bg_input"], fg=self.colors["text"],
                                 relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                                 command=self._new_conversation)
        btn_new_chat.pack(side=tk.LEFT)

        # Input + send
        input_row = tk.Frame(input_frame, bg=self.colors["bg_secondary"])
        input_row.pack(fill=tk.X, padx=10, pady=(5, 8))

        self.chat_input = tk.Text(input_row, font=("Segoe UI", 11),
                                  bg=self.colors["bg_input"], fg=self.colors["text"],
                                  insertbackground=self.colors["text"],
                                  relief=tk.FLAT, height=2, padx=10, pady=8,
                                  wrap=tk.WORD)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_input.bind("<Return>", self._on_enter)
        self.chat_input.bind("<Shift-Return>", lambda e: None)  # Allow newline with shift

        send_btn = tk.Button(input_row, text="Enviar ➤", font=("Segoe UI", 11, "bold"),
                             bg=self.colors["accent"], fg="white",
                             activebackground=self.colors["accent_hover"],
                             relief=tk.FLAT, padx=15, pady=8, cursor="hand2",
                             command=self._send_message)
        send_btn.pack(side=tk.RIGHT, padx=(8, 0))

    def _build_files_view(self):
        self.files_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        header = tk.Frame(self.files_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📁 Arquivos Monitorados", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        btn_frame = tk.Frame(header, bg=self.colors["bg_secondary"])
        btn_frame.pack(side=tk.RIGHT, padx=15)

        tk.Button(btn_frame, text="📂 Abrir Pasta", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text"],
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  command=self._open_watch_folder).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="📥 Adicionar Arquivo", font=("Segoe UI", 9),
                  bg=self.colors["accent"], fg="white",
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  command=self._add_file_to_watch).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="🔄 Atualizar", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text"],
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  command=self._refresh_files).pack(side=tk.LEFT, padx=2)

        # File list
        list_frame = tk.Frame(self.files_view, bg=self.colors["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.files_list = scrolledtext.ScrolledText(
            list_frame, wrap=tk.WORD, font=("Consolas", 10),
            bg=self.colors["bg_secondary"], fg=self.colors["text"],
            relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED
        )
        self.files_list.pack(fill=tk.BOTH, expand=True)

    def _build_search_view(self):
        self.search_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        header = tk.Frame(self.search_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🔍 Buscar na Base de Conhecimento", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        # Search input
        search_frame = tk.Frame(self.search_view, bg=self.colors["bg"])
        search_frame.pack(fill=tk.X, padx=10, pady=10)

        self.search_entry = tk.Entry(search_frame, font=("Segoe UI", 12),
                                     bg=self.colors["bg_input"], fg=self.colors["text"],
                                     insertbackground=self.colors["text"], relief=tk.FLAT)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        tk.Button(search_frame, text="Buscar", font=("Segoe UI", 11, "bold"),
                  bg=self.colors["accent"], fg="white", relief=tk.FLAT,
                  padx=15, pady=6, cursor="hand2",
                  command=self._do_search).pack(side=tk.RIGHT)

        # Results
        self.search_results = scrolledtext.ScrolledText(
            self.search_view, wrap=tk.WORD, font=("Segoe UI", 11),
            bg=self.colors["bg"], fg=self.colors["text"],
            relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED
        )
        self.search_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _build_restrictions_view(self):
        self.restrictions_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        header = tk.Frame(self.restrictions_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="⚙️ Restrições do Agente", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        # Info
        info_frame = tk.Frame(self.restrictions_view, bg=self.colors["bg"])
        info_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(info_frame, text="Defina as regras que o agente deve seguir. Uma restrição por linha.",
                 font=("Segoe UI", 10), bg=self.colors["bg"],
                 fg=self.colors["text_secondary"]).pack(anchor="w")

        # Restrictions editor
        self.restrictions_editor = scrolledtext.ScrolledText(
            self.restrictions_view, wrap=tk.WORD, font=("Segoe UI", 11),
            bg=self.colors["bg_input"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief=tk.FLAT,
            padx=15, pady=10
        )
        self.restrictions_editor.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Load current restrictions
        restrictions = self.config.get("restrictions", [])
        self.restrictions_editor.insert(tk.END, "\n".join(restrictions))

        # Buttons
        btn_frame = tk.Frame(self.restrictions_view, bg=self.colors["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="💾 Salvar Restrições", font=("Segoe UI", 11, "bold"),
                  bg=self.colors["success"], fg="white", relief=tk.FLAT,
                  padx=15, pady=6, cursor="hand2",
                  command=self._save_restrictions).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(btn_frame, text="➕ Adicionar Comando Permitido", font=("Segoe UI", 10),
                  bg=self.colors["bg_input"], fg=self.colors["text"], relief=tk.FLAT,
                  padx=10, pady=4, cursor="hand2",
                  command=self._add_allowed_command).pack(side=tk.LEFT, padx=5)

    def _build_memory_view(self):
        self.memory_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        header = tk.Frame(self.memory_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📊 Memória do Agente", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        tk.Button(header, text="🔄 Atualizar", font=("Segoe UI", 9),
                  bg=self.colors["bg_input"], fg=self.colors["text"],
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  command=self._refresh_memory).pack(side=tk.RIGHT, padx=15)

        # Memory content
        self.memory_display = scrolledtext.ScrolledText(
            self.memory_view, wrap=tk.WORD, font=("Consolas", 10),
            bg=self.colors["bg"], fg=self.colors["text"],
            relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED
        )
        self.memory_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _build_web_view(self):
        self.web_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        header = tk.Frame(self.web_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🌐 Navegação Web", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        # URL/Search input
        input_frame = tk.Frame(self.web_view, bg=self.colors["bg"])
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.web_input = tk.Entry(input_frame, font=("Segoe UI", 12),
                                  bg=self.colors["bg_input"], fg=self.colors["text"],
                                  insertbackground=self.colors["text"], relief=tk.FLAT)
        self.web_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
        self.web_input.insert(0, "Digite uma URL ou termo de busca...")
        self.web_input.bind("<FocusIn>", lambda e: self.web_input.delete(0, tk.END) if self.web_input.get().startswith("Digite") else None)
        self.web_input.bind("<Return>", lambda e: self._do_web_action())

        tk.Button(input_frame, text="🔍 Buscar", font=("Segoe UI", 10),
                  bg=self.colors["accent"], fg="white", relief=tk.FLAT,
                  padx=10, pady=5, cursor="hand2",
                  command=lambda: self._do_web_action("search")).pack(side=tk.LEFT, padx=2)

        tk.Button(input_frame, text="🌐 Abrir URL", font=("Segoe UI", 10),
                  bg=self.colors["bg_input"], fg=self.colors["text"], relief=tk.FLAT,
                  padx=10, pady=5, cursor="hand2",
                  command=lambda: self._do_web_action("fetch")).pack(side=tk.LEFT, padx=2)

        # Web results
        self.web_display = scrolledtext.ScrolledText(
            self.web_view, wrap=tk.WORD, font=("Segoe UI", 11),
            bg=self.colors["bg"], fg=self.colors["text"],
            relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED
        )
        self.web_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    def _build_terminal_view(self):
        self.terminal_view = tk.Frame(self.content_frame, bg=self.colors["bg"])

        header = tk.Frame(self.terminal_view, bg=self.colors["bg_secondary"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🖥️ Terminal Local", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["bg_secondary"], fg=self.colors["text"]).pack(side=tk.LEFT, padx=15, pady=10)

        tk.Label(header, text=f"CWD: {self.task_executor.working_dir}", font=("Consolas", 9),
                 bg=self.colors["bg_secondary"], fg=self.colors["text_secondary"]).pack(side=tk.RIGHT, padx=15)

        # Command input
        cmd_frame = tk.Frame(self.terminal_view, bg=self.colors["bg"])
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(cmd_frame, text="$", font=("Consolas", 14, "bold"),
                 bg=self.colors["bg"], fg=self.colors["accent"]).pack(side=tk.LEFT, padx=(0, 5))

        self.cmd_input = tk.Entry(cmd_frame, font=("Consolas", 12),
                                  bg=self.colors["bg_input"], fg=self.colors["text"],
                                  insertbackground=self.colors["text"], relief=tk.FLAT)
        self.cmd_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
        self.cmd_input.bind("<Return>", lambda e: self._execute_command())

        tk.Button(cmd_frame, text="Executar ▶", font=("Segoe UI", 10, "bold"),
                  bg=self.colors["accent"], fg="white", relief=tk.FLAT,
                  padx=12, pady=5, cursor="hand2",
                  command=self._execute_command).pack(side=tk.RIGHT)

        # Terminal output
        self.terminal_output = scrolledtext.ScrolledText(
            self.terminal_view, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0d1117", fg="#58a6ff",
            insertbackground="#58a6ff", relief=tk.FLAT,
            padx=15, pady=10, state=tk.DISABLED
        )
        self.terminal_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.terminal_output.tag_configure("command", foreground="#58a6ff", font=("Consolas", 10, "bold"))
        self.terminal_output.tag_configure("stdout", foreground="#c9d1d9")
        self.terminal_output.tag_configure("stderr", foreground="#f85149")
        self.terminal_output.tag_configure("success", foreground="#3fb950")
        self.terminal_output.tag_configure("error", foreground="#f85149")

    # === View switching ===
    def _hide_all_views(self):
        for view in [self.chat_view, self.files_view, self.search_view,
                     self.restrictions_view, self.memory_view, self.web_view,
                     self.terminal_view]:
            view.pack_forget()

    def _show_view(self, view):
        self._hide_all_views()
        view.pack(fill=tk.BOTH, expand=True)

    def _show_chat(self): self._show_view(self.chat_view)
    def _show_files(self):
        self._show_view(self.files_view)
        self._refresh_files()
    def _show_search(self): self._show_view(self.search_view)
    def _show_restrictions(self): self._show_view(self.restrictions_view)
    def _show_memory(self):
        self._show_view(self.memory_view)
        self._refresh_memory()
    def _show_web(self): self._show_view(self.web_view)
    def _show_terminal(self): self._show_view(self.terminal_view)

    # === Chat functionality ===
    def _append_chat(self, sender, message, tag_prefix="ai"):
        self.chat_display.configure(state=tk.NORMAL)
        name_tag = f"{tag_prefix}_name"
        msg_tag = f"{tag_prefix}_msg"

        self.chat_display.insert(tk.END, f"\n{'━' * 50}\n", "separator")
        self.chat_display.insert(tk.END, f" {sender}\n", name_tag)
        self.chat_display.insert(tk.END, f"{message}\n\n", msg_tag)
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _append_system(self, message):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"  ⚙ {message}\n", "system")
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _send_message(self):
        user_text = self.chat_input.get("1.0", tk.END).strip()
        if not user_text:
            return

        self.chat_input.delete("1.0", tk.END)
        self._append_chat("Você", user_text, "user")
        self.memory.add_message("user", user_text)

        # Check for special commands
        if user_text.startswith("/"):
            self._handle_command(user_text)
            return

        # Process with AI in background thread
        threading.Thread(target=self._process_message, args=(user_text,), daemon=True).start()

    def _process_message(self, user_text):
        self.root.after(0, lambda: self._append_system("Pensando..."))

        # Check if the message involves task execution
        context = self._build_context(user_text)

        # Check if AI wants to execute commands (look for patterns)
        result = self.ai.send_message(user_text, context=context)

        if result["success"]:
            response = result["text"]
            self.memory.add_message("assistant", response)

            # Check if response contains command suggestions
            self._check_and_execute_commands(response)

            self.root.after(0, lambda: self._append_chat("🧠 Kai", response, "ai"))
        else:
            error = result.get("error", "Erro desconhecido")
            self.root.after(0, lambda: self._append_chat("❌ Erro", error, "error"))

        self.root.after(0, self._update_stats)

    def _build_context(self, user_text):
        """Build context from memory and knowledge base."""
        context_parts = []

        # Search knowledge base for relevant info
        knowledge = self.memory.search_knowledge(user_text, limit=3)
        if knowledge:
            context_parts.append("=== CONHECIMENTO RELEVANTE ===")
            for k in knowledge:
                context_parts.append(f"[{k['source']}] {k['content'][:500]}")
            context_parts.append("=== FIM DO CONHECIMENTO ===\n")

        # Recent conversation history
        recent = self.memory.get_recent_messages(limit=10)
        if len(recent) > 1:
            context_parts.append("=== HISTÓRICO RECENTE ===")
            for msg in recent[-6:-1]:  # Last 5 before current
                role = "Usuário" if msg['role'] == 'user' else "Assistente"
                context_parts.append(f"{role}: {msg['content'][:300]}")
            context_parts.append("=== FIM DO HISTÓRICO ===\n")

        return "\n".join(context_parts) if context_parts else None

    def _check_and_execute_commands(self, response):
        """Check if AI response suggests executing commands."""
        import re
        # Look for code blocks with shell commands
        cmd_patterns = re.findall(r'```(?:bash|sh|cmd|powershell)?\n(.+?)```', response, re.DOTALL)
        for cmd in cmd_patterns:
            cmd = cmd.strip()
            if cmd and any(cmd.startswith(c) for c in self.config.get("allowed_commands", [])):
                result = self.task_executor.execute_command(cmd)
                if result["success"]:
                    self.root.after(0, lambda r=result: self._append_system(
                        f"Comando executado: {cmd[:50]}...\n{r['stdout'][:200]}"))

    def _handle_command(self, text):
        """Handle special slash commands."""
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/clear":
            self._clear_chat()
        elif cmd == "/reset":
            self.ai.reset_chat()
            self.ai.start_chat()
            self._append_system("Conversa reiniciada.")
        elif cmd == "/files":
            self._show_files()
        elif cmd == "/search":
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, arg)
            self._show_search()
            self._do_search()
        elif cmd == "/exec":
            self._show_terminal()
            self.cmd_input.delete(0, tk.END)
            self.cmd_input.insert(0, arg)
            self._execute_command()
        elif cmd == "/help":
            help_text = """Comandos disponíveis:
/clear - Limpar chat
/reset - Reiniciar conversa
/files - Ver arquivos monitorados
/search <termo> - Buscar na base de conhecimento
/exec <comando> - Executar comando no terminal
/help - Mostrar esta ajuda"""
            self._append_system(help_text)
        else:
            self._append_system(f"Comando desconhecido: {cmd}. Digite /help para ver comandos disponíveis.")

    def _on_enter(self, event):
        if not event.state & 0x1:  # Shift not pressed
            self._send_message()
            return "break"

    def _attach_file(self):
        filepath = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[
                ("Todos os arquivos", "*.*"),
                ("Texto", "*.txt *.md *.py *.js *.json *.csv *.html *.css"),
                ("Documentos", "*.pdf *.docx"),
                ("Dados", "*.json *.xml *.yaml *.csv")
            ]
        )
        if filepath:
            self._process_attached_file(filepath)

    def _process_attached_file(self, filepath):
        self._append_system(f"Processando arquivo: {os.path.basename(filepath)}...")
        threading.Thread(target=self._do_process_file, args=(filepath,), daemon=True).start()

    def _do_process_file(self, filepath):
        result = self.file_processor.read_file(filepath)
        if result["success"]:
            content = result["content"]
            filename = os.path.basename(filepath)

            # Save to memory
            self.memory.add_file(filename, filepath, result.get("type"),
                                content_preview=content[:1000])

            # AI analysis
            analysis = self.ai.analyze_file_content(content, filename)
            if analysis["success"]:
                self.memory.add_knowledge(filename, content[:5000], category="file")

            self.root.after(0, lambda: self._append_chat(
                "📎 Arquivo Processado",
                f"**{filename}** analisado com sucesso.\n\n"
                f"Tipo: {result.get('type', 'desconhecido')}\n"
                f"Tamanho: {len(content)} caracteres\n\n"
                f"**Análise da IA:**\n{analysis.get('text', 'Erro na análise') if analysis['success'] else analysis.get('error', 'Erro')}",
                "system"
            ))
        else:
            self.root.after(0, lambda: self._append_chat(
                "❌ Erro", f"Falha ao processar arquivo: {result['error']}", "error"))

        self.root.after(0, self._update_stats)

    def _clear_chat(self):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.configure(state=tk.DISABLED)

    def _new_conversation(self):
        self._clear_chat()
        self.ai.reset_chat()
        self.ai.start_chat()
        self._append_system("Nova conversa iniciada. O conhecimento acumulado permanece disponível.")

    def _load_history_to_chat(self):
        recent = self.memory.get_recent_messages(limit=20)
        if recent:
            self._append_system(f"Carregadas {len(recent)} mensagens do histórico.")
            for msg in recent[-10:]:  # Show last 10
                if msg['role'] == 'user':
                    self._append_chat("Você", msg['content'], "user")
                else:
                    self._append_chat("🧠 Kai", msg['content'], "ai")

    # === Files functionality ===
    def _refresh_files(self):
        files = self.file_processor.list_files()
        self.files_list.configure(state=tk.NORMAL)
        self.files_list.delete("1.0", tk.END)

        if not files:
            self.files_list.insert(tk.END, "Nenhum arquivo na pasta monitorada.\n\n")
            self.files_list.insert(tk.END, f"Pasta: {self.file_processor.watch_folder}\n")
            self.files_list.insert(tk.END, "Use '📥 Adicionar Arquivo' para começar.")
        else:
            self.files_list.insert(tk.END, f"📁 {len(files)} arquivo(s) encontrado(s)\n")
            self.files_list.insert(tk.END, f"Pasta: {self.file_processor.watch_folder}\n\n")

            for f in files:
                size = f['size']
                if size > 1024*1024:
                    size_str = f"{size/1024/1024:.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"

                self.files_list.insert(tk.END, f"  📄 {f['name']}\n")
                self.files_list.insert(tk.END, f"     Tamanho: {size_str} | Tipo: {f['extension']}\n")
                self.files_list.insert(tk.END, f"     Modificado: {f['modified']}\n\n")

        self.files_list.configure(state=tk.DISABLED)

    def _open_watch_folder(self):
        path = os.path.abspath(self.file_processor.watch_folder)
        os.makedirs(path, exist_ok=True)
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])

    def _add_file_to_watch(self):
        filepath = filedialog.askopenfilename(title="Selecionar arquivo para monitorar")
        if filepath:
            import shutil
            dest = os.path.join(self.file_processor.watch_folder, os.path.basename(filepath))
            shutil.copy2(filepath, dest)
            self._append_system(f"Arquivo adicionado: {os.path.basename(filepath)}")
            self._refresh_files()

    # === Search functionality ===
    def _do_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        self.search_results.configure(state=tk.NORMAL)
        self.search_results.delete("1.0", tk.END)
        self.search_results.insert(tk.END, f"🔍 Buscando: '{query}'...\n\n")

        # Search knowledge
        knowledge = self.memory.search_knowledge(query)
        if knowledge:
            self.search_results.insert(tk.END, f"📚 Conhecimento ({len(knowledge)} resultados):\n\n")
            for k in knowledge:
                self.search_results.insert(tk.END, f"  [{k['category']}] {k['source']}\n")
                self.search_results.insert(tk.END, f"  {k['content'][:300]}...\n\n")

        # Search files
        file_results = self.file_processor.search_in_files(query)
        if file_results:
            self.search_results.insert(tk.END, f"\n📁 Arquivos ({len(file_results)} encontrados):\n\n")
            for r in file_results:
                self.search_results.insert(tk.END, f"  📄 {r['file']} ({r['total_matches']} correspondências)\n")
                for m in r['matches'][:3]:
                    self.search_results.insert(tk.END, f"    L{m['line_num']}: {m['text'][:100]}\n")
                self.search_results.insert(tk.END, "\n")

        if not knowledge and not file_results:
            self.search_results.insert(tk.END, "Nenhum resultado encontrado.")

        self.search_results.configure(state=tk.DISABLED)

    # === Restrictions functionality ===
    def _save_restrictions(self):
        text = self.restrictions_editor.get("1.0", tk.END).strip()
        restrictions = [r.strip() for r in text.split("\n") if r.strip()]
        self.config["restrictions"] = restrictions
        self.ai.set_restrictions(restrictions)
        self._save_config()
        messagebox.showinfo("Sucesso", f"{len(restrictions)} restrições salvas!")

    def _add_allowed_command(self):
        cmd = simpledialog.askstring("Adicionar Comando", "Nome do comando permitido:")
        if cmd:
            if "allowed_commands" not in self.config:
                self.config["allowed_commands"] = []
            self.config["allowed_commands"].append(cmd.strip())
            self.task_executor.allowed_commands = self.config["allowed_commands"]
            self._save_config()
            self._append_system(f"Comando permitido adicionado: {cmd}")

    # === Memory functionality ===
    def _refresh_memory(self):
        stats = self.memory.get_stats()
        recent_actions = self.memory.get_recent_actions(limit=10)

        self.memory_display.configure(state=tk.NORMAL)
        self.memory_display.delete("1.0", tk.END)

        self.memory_display.insert(tk.END, "📊 ESTATÍSTICAS DA MEMÓRIA\n")
        self.memory_display.insert(tk.END, "═" * 40 + "\n\n")
        self.memory_display.insert(tk.END, f"  💬 Conversas: {stats['conversations']} mensagens\n")
        self.memory_display.insert(tk.END, f"  📚 Conhecimento: {stats['knowledge']} entradas\n")
        self.memory_display.insert(tk.END, f"  📁 Arquivos: {stats['files']} indexados\n")
        self.memory_display.insert(tk.END, f"  ⚡ Ações: {stats['actions']} registradas\n\n")

        if recent_actions:
            self.memory_display.insert(tk.END, "⚡ AÇÕES RECENTES\n")
            self.memory_display.insert(tk.END, "═" * 40 + "\n\n")
            for action in recent_actions:
                self.memory_display.insert(tk.END, f"  [{action['timestamp'][:16]}] {action['action_type']}\n")
                self.memory_display.insert(tk.END, f"    {action['description'][:100]}\n\n")

        self.memory_display.configure(state=tk.DISABLED)

    # === Web functionality ===
    def _do_web_action(self, action_type=None):
        query = self.web_input.get().strip()
        if not query or query.startswith("Digite"):
            return

        if not action_type:
            action_type = "search" if not query.startswith("http") else "fetch"

        self.web_display.configure(state=tk.NORMAL)
        self.web_display.delete("1.0", tk.END)
        self.web_display.insert(tk.END, f"Processando: {query}\n\n")
        self.web_display.configure(state=tk.DISABLED)

        threading.Thread(target=self._do_web_thread, args=(query, action_type), daemon=True).start()

    def _do_web_thread(self, query, action_type):
        if action_type == "search":
            result = self.task_executor.web_search(query)
            self.root.after(0, lambda: self._display_search_results(result, query))
        else:
            result = self.task_executor.fetch_webpage(query)
            self.root.after(0, lambda: self._display_fetch_results(result, query))

    def _display_search_results(self, result, query):
        self.web_display.configure(state=tk.NORMAL)
        self.web_display.delete("1.0", tk.END)

        if result["success"]:
            self.web_display.insert(tk.END, f"🔍 Resultados para: '{query}'\n\n")
            for i, r in enumerate(result["results"], 1):
                self.web_display.insert(tk.END, f"{i}. {r['title']}\n")
                self.web_display.insert(tk.END, f"   {r['url']}\n")
                self.web_display.insert(tk.END, f"   {r['snippet']}\n\n")

            # Save to memory
            self.memory.add_knowledge("web_search", json.dumps(result["results"], ensure_ascii=False), category="web")
        else:
            self.web_display.insert(tk.END, f"❌ Erro: {result['error']}")

        self.web_display.configure(state=tk.DISABLED)

    def _display_fetch_results(self, result, url):
        self.web_display.configure(state=tk.NORMAL)
        self.web_display.delete("1.0", tk.END)

        if result["success"]:
            self.web_display.insert(tk.END, f"🌐 {result['title']}\n")
            self.web_display.insert(tk.END, f"URL: {url}\n")
            self.web_display.insert(tk.END, f"Tamanho: {result['total_length']} caracteres\n\n")
            self.web_display.insert(tk.END, "═" * 50 + "\n\n")
            self.web_display.insert(tk.END, result["content"])

            # Save to memory
            self.memory.add_knowledge(url, result["content"][:5000], category="webpage")
        else:
            self.web_display.insert(tk.END, f"❌ Erro: {result['error']}")

        self.web_display.configure(state=tk.DISABLED)

    # === Terminal functionality ===
    def _execute_command(self):
        cmd = self.cmd_input.get().strip()
        if not cmd:
            return

        self.cmd_input.delete(0, tk.END)

        self.terminal_output.configure(state=tk.NORMAL)
        self.terminal_output.insert(tk.END, f"$ {cmd}\n", "command")

        result = self.task_executor.execute_command(cmd)

        if result["success"]:
            if result.get("stdout"):
                self.terminal_output.insert(tk.END, result["stdout"], "stdout")
            if result.get("stderr"):
                self.terminal_output.insert(tk.END, result["stderr"], "stderr")
            self.terminal_output.insert(tk.END, "✓ Concluído\n\n", "success")
        else:
            self.terminal_output.insert(tk.END, f"✗ {result['error']}\n\n", "error")

        self.terminal_output.configure(state=tk.DISABLED)
        self.terminal_output.see(tk.END)

    # === Utility ===
    def _update_stats(self):
        stats = self.memory.get_stats()
        stats_text = (
            f"💬 {stats['conversations']} msgs\n"
            f"📚 {stats['knowledge']} conhec.\n"
            f"📁 {stats['files']} arquivos\n"
            f"⚡ {stats['actions']} ações"
        )
        self.stats_label.configure(text=stats_text)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self.memory.close()
        self.root.destroy()


def main():
    # Ensure watch folder exists
    os.makedirs("watched_files", exist_ok=True)

    app = LeonAIAgent()
    app.run()


if __name__ == "__main__":
    main()
