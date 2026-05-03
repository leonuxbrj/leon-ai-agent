"""
Task executor - handles local commands, web searches, and task automation.
"""

import subprocess
import os
import json
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

    def _log_action(self, action_type, description, result=None):
        entry = {
            "type": action_type,
            "description": description,
            "result": str(result)[:500] if result else None,
            "timestamp": datetime.now().isoformat()
        }
        self.action_log.append(entry)
        return entry

    def _is_command_allowed(self, command):
        """Check if a command is allowed based on config."""
        cmd_lower = command.lower().strip()

        # Check blocked commands first
        for blocked in self.blocked_commands:
            if blocked.lower() in cmd_lower:
                return False, f"Comando bloqueado: contém '{blocked}'"

        # If allowlist is empty, allow all non-blocked
        if not self.allowed_commands:
            return True, ""

        # Check if base command is in allowlist
        base_cmd = cmd_lower.split()[0] if cmd_lower.split() else ""
        for allowed in self.allowed_commands:
            if base_cmd == allowed.lower() or base_cmd.startswith(allowed.lower()):
                return True, ""

        return False, f"Comando '{base_cmd}' não está na lista de comandos permitidos"

    def execute_command(self, command, timeout=30):
        """Execute a local shell command."""
        allowed, reason = self._is_command_allowed(command)
        if not allowed:
            self._log_action("command_blocked", command, reason)
            return {"success": False, "error": reason}

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )
            output = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": command
            }
            self._log_action("command", command, result.stdout[:200] if result.stdout else result.stderr[:200])
            return output

        except subprocess.TimeoutExpired:
            self._log_action("command_timeout", command)
            return {"success": False, "error": f"Comando expirou após {timeout}s"}
        except Exception as e:
            self._log_action("command_error", command, str(e))
            return {"success": False, "error": str(e)}

    def web_search(self, query, num_results=5):
        """Search the web using DuckDuckGo."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            for result in soup.select('.result'):
                title_elem = result.select_one('.result__title a')
                snippet_elem = result.select_one('.result__snippet')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    # Clean DuckDuckGo redirect URLs
                    if 'uddg=' in link:
                        link = link.split('uddg=')[1].split('&')[0]

                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet
                    })

                if len(results) >= num_results:
                    break

            self._log_action("web_search", query, f"{len(results)} resultados")
            return {"success": True, "results": results}

        except Exception as e:
            self._log_action("web_search_error", query, str(e))
            return {"success": False, "error": str(e)}

    def fetch_webpage(self, url, max_chars=10000):
        """Fetch and extract text content from a webpage."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove scripts and styles
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            text = soup.get_text(separator='\n', strip=True)
            # Clean up excessive whitespace
            text = re.sub(r'\n{3,}', '\n\n', text)

            self._log_action("fetch_webpage", url, f"{len(text)} chars")
            return {
                "success": True,
                "title": soup.title.string if soup.title else "Sem título",
                "content": text[:max_chars],
                "total_length": len(text)
            }

        except Exception as e:
            self._log_action("fetch_webpage_error", url, str(e))
            return {"success": False, "error": str(e)}

    def create_file(self, filepath, content):
        """Create or overwrite a file."""
        try:
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self._log_action("create_file", filepath, f"{len(content)} chars")
            return {"success": True, "filepath": filepath, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def read_file(self, filepath):
        """Read a file's content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"success": True, "content": content, "filepath": filepath}
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
            return {"success": True, "content": content, "filepath": filepath}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, path=None):
        """List contents of a directory."""
        target = path or self.working_dir
        try:
            items = []
            for item in os.listdir(target):
                full_path = os.path.join(target, item)
                stat = os.stat(full_path)
                items.append({
                    "name": item,
                    "type": "dir" if os.path.isdir(full_path) else "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            return {"success": True, "path": target, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def change_directory(self, path):
        """Change working directory."""
        try:
            abs_path = os.path.abspath(path)
            if os.path.isdir(abs_path):
                self.working_dir = abs_path
                return {"success": True, "cwd": abs_path}
            else:
                return {"success": False, "error": f"Diretório não existe: {abs_path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_action_log(self, last_n=20):
        """Get recent action log."""
        return self.action_log[-last_n:]

    def get_system_info(self):
        """Get basic system information."""
        import platform
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cwd": self.working_dir
        }
