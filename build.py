"""
Build script - generates the .exe for Windows distribution.
Run this on a Windows machine with Python installed.
"""

import subprocess
import sys
import os

def install_requirements():
    """Install all required packages."""
    print("📦 Instalando dependências...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_exe():
    """Build the executable using PyInstaller."""
    print("🔨 Gerando executável...")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=LeonAIAgent",
        "--icon=NONE",
        "--add-data=config.json;.",
        "--add-data=memory.py;.",
        "--add-data=ai_engine.py;.",
        "--add-data=file_processor.py;.",
        "--add-data=task_executor.py;.",
        "--hidden-import=google.generativeai",
        "--hidden-import=chardet",
        "--hidden-import=PyPDF2",
        "--hidden-import=docx",
        "--hidden-import=watchdog",
        "--hidden-import=bs4",
        "--hidden-import=requests",
        "--noconfirm",
        "main.py"
    ]

    subprocess.check_call(cmd)
    print("\n✅ Executável gerado em: dist/LeonAIAgent.exe")

def main():
    if not os.path.exists("config.json"):
        print("❌ config.json não encontrado!")
        return

    install_requirements()
    build_exe()

    print("\n" + "=" * 50)
    print("🎉 BUILD CONCLUÍDO!")
    print("=" * 50)
    print("\nO executável está na pasta 'dist/'.")
    print("Copie 'LeonAIAgent.exe' para onde quiser e execute.")
    print("\n⚠️  O arquivo config.json será embutido no exe.")
    print("   Se precisar alterar configurações, rebuild após editar.")

if __name__ == "__main__":
    main()
