@echo off
REM ==========================================================
REM  Abre no navegador todas as URLs da POC.
REM  Rode depois do "docker compose up -d" (na raiz do projeto).
REM ==========================================================
cd /d "%~dp0"

echo Conferindo se os containers estao no ar...
docker compose ps --format "table {{.Service}}\t{{.Status}}" 2>nul
if errorlevel 1 (
  echo.
  echo O Docker nao respondeu. Abra o Docker Desktop e rode: docker compose up -d
  pause
  exit /b 1
)
echo.

REM Front-end (React)
start "" "http://localhost:3000"
REM Swagger (testar os endpoints)
start "" "http://localhost:8000/docs"
REM ReDoc (documentacao da API, so leitura)
start "" "http://localhost:8000/redoc"
REM Status da API (SQL Server + RabbitMQ)
start "" "http://localhost:8000/health"
REM APIs de consulta
start "" "http://localhost:8000/lotes"
start "" "http://localhost:8000/dashboard"
REM Painel do RabbitMQ (filas) - usuario e senha do .env
start "" "http://localhost:15672/#/queues"

echo URLs abertas:
echo   Front-end ........ http://localhost:3000
echo   Swagger .......... http://localhost:8000/docs
echo   ReDoc ............ http://localhost:8000/redoc
echo   Status (health) .. http://localhost:8000/health
echo   Lotes ............ http://localhost:8000/lotes
echo   Dashboard ........ http://localhost:8000/dashboard
echo   Filas (RabbitMQ) . http://localhost:15672
echo.
echo O painel do RabbitMQ pede o RABBIT_USER e o RABBIT_PASSWORD do arquivo .env
pause
