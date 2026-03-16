@echo off
setlocal enabledelayedexpansion
REM ============================================================
REM Script: Rebuild & Auto-Commit ETL DockTech
REM Objetivo: Resetar o indice e forçar atualização total no GitHub
REM ============================================================

REM Definir caminho do projeto
set PROJETO_PATH=C:\Users\lucas.pinto\Desktop\Site_docktech_ligacoes

REM Entrar na pasta do projeto
pushd "%PROJETO_PATH%"

cls
echo ============================================================
echo 1. LIMPANDO CACHE E PREPARANDO REBUILD...
echo ============================================================

REM Remove o índice atual do Git (não deleta seus arquivos, apenas a lista de rastreio)
git rm -r --cached . >nul 2>&1

REM Criar .gitignore caso nao exista
if not exist .gitignore (
    echo __pycache__/ > .gitignore
    echo *.pyc >> .gitignore
    echo .streamlit/ >> .gitignore
    echo venv/ >> .gitignore
)

REM Definir mensagem de commit
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%b-%%a)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a%%b)
set commit_message=Rebuild Repository: %mydate% %mytime%

echo.
echo ============================================================
echo 2. EXECUTANDO SCRIPTS DE ETL E CONSOLIDACAO...
echo ============================================================
python "executa_todos.py"
python "nivel_dois_bases_app\quadro_geral.py"

echo.
echo ============================================================
echo 3. RECONSTRUINDO INDICE E FORCANDO PUSH...
echo ============================================================

REM Adiciona tudo novamente do zero (Rebuild do índice)
git add --all

echo Fazendo commit de reconstrucao...
git commit -m "%commit_message%"

echo Enviando para GitHub (Force Push)...
REM O --force garante que o GitHub aceite o estado local como a verdade
git push origin main --force

echo.
echo ============================================================
echo REBUILD CONCLUIDO! [%mydate% %mytime%]
echo >>> O repositório foi reconstruído e forçado para a nuvem.
echo ============================================================
echo.

popd
pause