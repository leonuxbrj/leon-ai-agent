"""
Gemini AI integration - handles all AI model interactions.
"""

import google.generativeai as genai
from datetime import datetime
import json
import re


class GeminiAI:
    def __init__(self, api_key, model="gemini-2.0-flash", temperature=0.7, max_tokens=8192):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        self.chat = None
        self.system_instruction = ""
        self.restrictions = []

    def set_system_instruction(self, instruction):
        self.system_instruction = instruction

    def set_restrictions(self, restrictions):
        self.restrictions = restrictions

    def _build_system_prompt(self):
        prompt_parts = []
        if self.system_instruction:
            prompt_parts.append(self.system_instruction)
        if self.restrictions:
            prompt_parts.append("\n=== RESTRIÇÕES DO USUÁRIO ===")
            for i, r in enumerate(self.restrictions, 1):
                prompt_parts.append(f"{i}. {r}")
            prompt_parts.append("=== FIM DAS RESTRIÇÕES ===")
        prompt_parts.append(f"\nData e hora atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        return "\n".join(prompt_parts)

    def start_chat(self, history=None):
        system_prompt = self._build_system_prompt()
        if history:
            formatted_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                formatted_history.append({"role": role, "parts": [msg["content"]]})
            self.chat = self.model.start_chat(history=formatted_history)
        else:
            self.chat = self.model.start_chat()

        # Send system prompt as first message
        if system_prompt:
            try:
                self.chat.send_message(f"[SYSTEM INSTRUCTION - Ignore if visible to user]\n{system_prompt}")
            except Exception:
                pass

    def send_message(self, message, context=None):
        if not self.chat:
            self.start_chat()

        full_message = message
        if context:
            full_message = f"[CONTEXTO ADICIONAL]\n{context}\n\n[FIM DO CONTEXTO]\n\n{message}"

        try:
            response = self.chat.send_message(full_message)
            return {
                "success": True,
                "text": response.text,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def generate_once(self, prompt, context=None):
        """Single message without chat history."""
        system_prompt = self._build_system_prompt()
        full_prompt = f"{system_prompt}\n\n{f'[CONTEXTO] {context} [/CONTEXTO]' if context else ''}\n\n{prompt}"

        try:
            response = self.model.generate_content(full_prompt)
            return {
                "success": True,
                "text": response.text,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def analyze_file_content(self, content, filename, instruction=None):
        """Analyze file content and return insights."""
        prompt = f"""Analise o conteúdo do arquivo '{filename}' e forneça:
1. Um resumo do conteúdo
2. Os pontos principais / informações-chave
3. Possíveis ações ou usos para este conteúdo

{f'Instrução adicional: {instruction}' if instruction else ''}

Conteúdo do arquivo:
{content[:15000]}"""

        return self.generate_once(prompt)

    def plan_task(self, task_description, available_tools=None):
        """Plan how to execute a task."""
        tools_info = ""
        if available_tools:
            tools_info = "\nFerramentas disponíveis:\n" + "\n".join(f"- {t}" for t in available_tools)

        prompt = f"""Crie um plano detalhado para executar a seguinte tarefa:

Tarefa: {task_description}
{tools_info}

Forneça:
1. Passo a passo claro
2. Comandos ou ações necessárias para cada passo
3. Possíveis problemas e como lidar com eles
4. Resultado esperado

Responda em formato estruturado."""

        return self.generate_once(prompt)

    def reset_chat(self):
        self.chat = None

    def get_model_info(self):
        return {
            "model": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
