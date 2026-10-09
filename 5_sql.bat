@echo off
REM ==========================================================
REM  5) SQL: abre o sqlcmd (cliente de linha de comando do
REM     SQL Server) dentro do container, ja no banco da POC.
REM     Nao precisa instalar nada nem digitar a senha: usa a
REM     senha que o proprio container recebeu do .env.
REM
REM     Digite a consulta e depois GO + Enter. Para sair: EXIT
REM ==========================================================
cd /d "%~dp0"
echo Conectando no SQL Server (banco poc_ingestao_proc_arquivo)...
echo Exemplos:
echo   SELECT id, nome_zip, status FROM lote ORDER BY id DESC;
echo   SELECT nome, status, fila, tipo_documental FROM arquivo WHERE lote_id = 7;
echo   GO
echo.
docker compose exec sqlserver bash -c "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $MSSQL_SA_PASSWORD -C -d poc_ingestao_proc_arquivo -W -s ' | '"
