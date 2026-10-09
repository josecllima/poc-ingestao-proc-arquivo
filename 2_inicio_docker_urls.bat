@echo off
REM ==========================================================
REM  2) INICIAR: abre o Docker (se estiver fechado), sobe os
REM     containers (recria so os que tiverem imagem nova do
REM     1_recompilar.bat), espera a API e o front-end e abre
REM     o painel com os links.
REM ==========================================================
cd /d "%~dp0"
call :docker_pronto || goto falhou

echo.
echo Subindo os containers...
docker compose up -d --remove-orphans || goto falhou
echo.
call :esperar_servicos
echo.
docker compose ps --format "table {{.Service}}\t{{.Status}}"
echo.

REM Abre a tela Painel do front-end, com os links para todas as outras (cada link abre em nova aba)
start "" "http://localhost:3000/#/painel"

echo Painel aberto: http://localhost:3000/#/painel
echo   (Front-end, Swagger, ReDoc, health, lotes, dashboard e RabbitMQ - cada link abre em nova aba)
echo.
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

REM ----------------------------------------------------------
REM  Sub-rotina: espera a API (ate 6 min) e o front-end (ate 3 min).
REM ----------------------------------------------------------
:esperar_servicos
echo Aguardando a API em http://localhost:8000/health ...
set /a es_tent=0
:es_api
curl -fs http://localhost:8000/health >nul 2>&1
if not errorlevel 1 goto es_api_ok
set /a es_tent+=1
if %es_tent% geq 72 (
    echo A API nao respondeu em 6 minutos. Veja: docker compose logs backend --tail 60
    goto es_front
)
timeout /t 5 /nobreak >nul
goto es_api
:es_api_ok
echo API pronta.
:es_front
echo Aguardando o front-end em http://localhost:3000 ...
set /a es_tent=0
:es_front_loop
curl -fs http://localhost:3000 >nul 2>&1
if not errorlevel 1 (
    echo Front-end pronto.
    exit /b 0
)
set /a es_tent+=1
if %es_tent% geq 36 (
    echo O front-end nao respondeu em 3 minutos. Veja: docker compose logs frontend --tail 60
    exit /b 0
)
timeout /t 5 /nobreak >nul
goto es_front_loop
