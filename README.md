# 🧠 Leon AI Agent

Agente local de IA powered by Gemini, com interface gráfica, processamento de arquivos, memória persistente e execução de tarefas.

## ⚡ Instalação Rápida (Windows)

### Opção 1: Executar direto do Python
```bash
# 1. Instale Python 3.10+ se não tiver: https://python.org
# 2. Abra o terminal na pasta do projeto
pip install -r requirements.txt
python main.py
```

### Opção 2: Gerar o .exe
```bash
pip install -r requirements.txt
pip install pyinstaller
python build.py
# O .exe estará na pasta dist/
```

## 🎯 Funcionalidades

### 💬 Chat com IA
- Conversa com Gemini (API externa)
- Entende contexto e histórico
- Executa tarefas a partir do chat
- Comandos: `/clear`, `/reset`, `/files`, `/search`, `/exec`, `/help`

### 📁 Monitoramento de Arquivos
- Arraste arquivos para a pasta `watched_files/`
- Use o botão "📎 Anexar Arquivo" no chat
- O agente lê, analisa e indexa automaticamente
- Suporta: TXT, MD, PY, JS, JSON, CSV, PDF, DOCX, e mais

### 🔍 Busca na Base de Conhecimento
- Busca em todos os arquivos indexados
- Busca no conhecimento acumulado pela IA
- Resultados salvos na memória persistente

### ⚙️ Restrições Personalizáveis
- Defina regras que o agente DEVE seguir
- Adicione/remove comandos permitidos
- Bloqueie comandos perigosos
- Tudo editável pela interface

### 📊 Memória Persistente
- Histórico de conversas salvo em SQLite
- Conhecimento acumulado por categoria
- Log de todas as ações executadas
- Estatísticas em tempo real

### 🌐 Navegação Web
- Busca na web (DuckDuckGo)
- Leitura de páginas web
- Conteúdo extraído e indexado automaticamente

### 🖥️ Terminal Local
- Execute comandos do sistema
- Comandos permitidos/bloqueados configuráveis
- Histórico de execução

## 📂 Estrutura do Projeto

```
leon-ai-agent/
├── main.py              # Interface principal (GUI)
├── ai_engine.py         # Integração com Gemini
├── memory.py            # Sistema de memória (SQLite)
├── file_processor.py    # Processamento de arquivos
├── task_executor.py     # Execução de comandos e web
├── config.json          # Configurações e API key
├── requirements.txt     # Dependências Python
├── build.py             # Script para gerar .exe
├── watched_files/       # Pasta de arquivos monitorados
└── memory.db            # Banco de dados (criado automaticamente)
```

## ⚙️ Configuração (config.json)

```json
{
  "api_key": "SUA_API_KEY_GEMINI",
  "model": "gemini-2.0-flash",
  "agent_name": "Leon AI Agent",
  "restrictions": [
    "Responda sempre em português brasileiro",
    "Seja direto e prático"
  ],
  "allowed_commands": ["dir", "ls", "python", "pip", "git"],
  "blocked_commands": ["format", "rm -rf /"]
}
```

## 🔐 Segurança

- API key armazenada apenas localmente
- Comandos de sistema filtrados por allowlist/blocklist
- Restrições personalizáveis pelo usuário
- Nenhum dado enviado para servidores terceiros (exceto Gemini API)

## 🚀 Primeiros Passos

1. Execute o aplicativo
2. A API key do Gemini já está configurada
3. Comece digitando no chat ou anexe um arquivo
4. Use `/help` para ver comandos disponíveis
5. Vá em "⚙️ Restrições" para personalizar o comportamento

---
Desenvolvido por Kai 🌊 para Leon
