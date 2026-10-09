@echo off
REM ==========================================================
REM  4) EXEMPLOS COM CARIMBO: gera lotes INEDITOS em
REM     exemplos\gerados\ - o ZIP e cada arquivo interno ganham
REM     o sufixo _ddmmaaaahhmmss e os dados mudam a cada vez.
REM     Use para enviar o mesmo cenario varias vezes sem cair
REM     na regra de duplicidade. (pasta fora do Git)
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

echo Gerando lotes de teste com carimbo de data e hora...
echo.
%PY% exemplos\gerar_exemplos.py --carimbo || goto falhou
echo.
start "" explorer "%~dp0exemplos\gerados"
pause
exit /b 0

:falhou
echo.
echo Algo falhou. Veja a mensagem acima.
pause
exit /b 1
