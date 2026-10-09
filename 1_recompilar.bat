@echo off
REM ==========================================================
REM  1) COMPILAR: so reconstroi as imagens (API, workers e
REM     front-end). Nao sobe nem para nenhum container.
REM     Use depois de mudar o codigo; em seguida rode o
REM     2_inicio_docker_urls.bat para subir com as imagens novas.
REM ==========================================================
cd /d "%~dp0"

REM O build precisa do motor do Docker: se estiver fechado, abre.
call :docker_pronto || goto falhou

echo.
echo Compilando as imagens...
docker compose build || goto falhou
echo.
echo Compilacao concluida.
echo Para subir os containers com as imagens novas e abrir o painel: 2_inicio_docker_urls.bat
pause
exit /b 0

:falhou
echo.
echo Algo falhou. Veja a mensagem acima.
pause
exit /b 1

REM ----------------------------------------------------------
REM  Sub-rotina: abre o Docker Desktop (se estiver fechado) e
REM  espera ele ficar pronto (ate 5 minutos).
REM ----------------------------------------------------------
:docker_pronto
docker info >nul 2>&1
if not errorlevel 1 (
    echo Docker ja esta rodando.
    exit /b 0
)
echo Iniciando o Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
    start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
) else (
    echo Nao encontrei o Docker Desktop em "%ProgramFiles%\Docker\Docker".
    echo Abra o Docker manualmente e rode este arquivo de novo.
    exit /b 1
)
set /a dk_tent=0
:dk_loop
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 (
    echo Docker pronto.
    exit /b 0
)
set /a dk_tent+=1
if %dk_tent% geq 60 (
    echo O Docker nao ficou pronto em 5 minutos.
    exit /b 1
)
echo   aguardando o Docker... (%dk_tent%/60)
set /a dk_resto=dk_tent %% 6
if %dk_resto%==0 call :dk_diag
goto dk_loop

REM Mostra a cada 30s se o Docker Desktop esta aberto e o erro do motor
:dk_diag
tasklist /fi "imagename eq Docker Desktop.exe" 2>nul | find /i "Docker Desktop.exe" >nul
if errorlevel 1 (
    echo   [!] O processo "Docker Desktop.exe" NAO esta rodando.
) else (
    echo   [i] Docker Desktop aberto, mas o motor ainda nao respondeu.
)
for /f "delims=" %%L in ('docker info 2^>^&1 ^| findstr /i "error"') do echo   [erro] %%L
exit /b 0
