@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo === Furyu · instalacao Windows ===
echo Pasta: %CD%
echo.

echo %CD% | findstr /I /C:"8662-B449" >nul
if %ERRORLEVEL%==0 (
  echo ERRO: parece o pendrive exFAT.
  echo Copie a pasta para o SSD, ex.: C:\Furyu2
  echo e rode este .bat LA.
  exit /b 1
)

if not exist "app.py" (
  echo ERRO: app.py nao encontrado. Copie a pasta inteira do pendrive.
  exit /b 1
)
if not exist "academic_search.py" (
  echo ERRO: falta academic_search.py ^(busca Oasisbr^).
  echo Copie a pasta ATUAL do pendrive, nao um clone antigo do GitHub.
  exit /b 1
)

where py >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python nao esta no PATH.
  echo Instale Python 3.12 e marque "Add python.exe to PATH".
  exit /b 1
)

py -3.12 --version
if errorlevel 1 (
  echo ERRO: precisa do Python 3.12 ^(py -3.12^).
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Criando .venv ...
  py -3.12 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
echo Instalando PyTorch CPU ...
pip install torch --index-url https://download.pytorch.org/whl/cpu
echo Instalando PaperQA + Streamlit ...
pip install -c constraints-cpu.txt --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

set "NEED_ENV=0"
if not exist ".env" set "NEED_ENV=1"
if exist ".env" (
  findstr /C:"/media/" ".env" >nul
  if not errorlevel 1 set "NEED_ENV=1"
  findstr /C:"pqa-linux" ".env" >nul
  if not errorlevel 1 set "NEED_ENV=1"
)
if "%NEED_ENV%"=="1" (
  copy /Y .env.example .env >nul
  echo Gerado .env do Windows a partir de .env.example
)

echo.
echo Pronto. Agora:
echo   1. Instale o Ollama e rode:  ollama pull qwen3.5:4b
echo   2. Edite o .env: CONTACT_EMAIL=seu.email@escola.edu.br
echo      ^(e-mail real; nao e login de usuario^)
echo   3. Rode:  rodar-windows.bat
echo      ou:    .venv\Scripts\activate
echo             streamlit run app.py
echo.
echo A tela e a mesma do Linux: enviar PDF, buscar Oasisbr, perguntar.
echo A busca precisa de internet. O Ollama e local.
echo.
endlocal
