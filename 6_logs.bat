@echo off
REM ==========================================================
REM  6) LOGS DE UM LOTE: junta os logs de todos os containers
REM     (API e workers) que citam o lote informado e salva em
REM     docs\evidencias-testes\logs-lote-<id>.txt
REM ==========================================================
cd /d "%~dp0"
set /p LOTE=Numero do lote: 
if "%LOTE%"=="" (
    echo Nenhum lote informado.
    pause
    exit /b 1
)
if not exist "docs\evidencias-testes" mkdir "docs\evidencias-testes"
set SAIDA=docs\evidencias-testes\logs-lote-%LOTE%.txt

echo Coletando os logs do lote %LOTE%...
if exist "%SAIDA%" del "%SAIDA%"
powershell -NoProfile -Command "[Console]::OutputEncoding=[Text.Encoding]::UTF8; docker compose logs --no-color --timestamps | Select-String -Pattern 'loteId=%LOTE%\b' | ForEach-Object { $_.Line } | Sort-Object { ($_ -split '\|',2)[1] } | Set-Content -Encoding utf8 '%SAIDA%'"

if not exist "%SAIDA%" type nul > "%SAIDA%"
for %%A in ("%SAIDA%") do if %%~zA==0 (
    echo Nenhuma linha encontrada para o lote %LOTE%.
    echo Confira o numero na tela Lotes, ou rode 1_recompilar.bat se as imagens forem antigas.
    pause
    exit /b 1
)
echo Salvo em %SAIDA%
start "" notepad "%SAIDA%"
pause
exit /b 0
