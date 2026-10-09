@echo off
REM ==========================================================
REM  3) EXEMPLOS CONVENCIONAIS: recria os ZIPs oficiais de teste
REM     em exemplos\ com nomes fixos (lote-valido.zip, ...).
REM     Sao os arquivos de teste que vao para o repositorio.
REM ==========================================================
cd /d "%~dp0"
REM Usa o "py" (instalador oficial do Python no Windows) ou, se nao houver, o "python"
set PY=
where py >nul 2>&1
if not errorlevel 1 (
    set PY=py
) else (
    where python >nul 2>&1
    if not errorlevel 1 set PY=python
)
if not defined PY (
    echo Python nao encontrado. Instale em https://www.python.org e marque "Add to PATH".
    pause
    exit /b 1
)

echo Gerando os ZIPs de teste convencionais...
echo.
%PY% exemplos\gerar_exemplos.py || goto falhou
echo.
start "" explorer "%~dp0exemplos"
pause
exit /b 0

:falhou
echo.
echo Algo falhou. Veja a mensagem acima.
pause
exit /b 1
