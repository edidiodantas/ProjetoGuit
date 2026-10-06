@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
  echo ERRO: rode install-windows.bat primeiro.
  exit /b 1
)
if not exist "academic_search.py" (
  echo ERRO: falta academic_search.py. Copie a pasta atual do pendrive.
  exit /b 1
)

call .venv\Scripts\activate.bat
echo Furyu — Ollama precisa estar aberto ^(localhost:11434^).
echo Abrindo http://localhost:8501 ...
streamlit run app.py
endlocal
