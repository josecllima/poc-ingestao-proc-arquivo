# Evidências de Testes

**Documento completo (prints + descrição de cada evidência): [`evidencias-de-testes.pdf`](evidencias-de-testes.pdf)**

Execução manual em ambiente local (Windows + Docker Desktop) com os ZIPs de [`exemplos/`](../../exemplos/README.md).
Rodada final: **09/10/2026, 18:09** — lotes 2002 a 2006, gerados com `4_gerar_documentos_outros.bat`.
O mesmo fluxo roda automaticamente a cada push no [CI](../../.github/workflows/ci.yml) (teste de ponta a ponta).

## Resultado da rodada final

| Lote | ZIP | Esperado | Obtido | Arquivos (sucesso / erros / ignorados) |
|---|---|---|---|---|
| 2002 | `lote-1mb_….zip` | CONCLUIDO | ✅ CONCLUIDO | 6 (6 / 0 / 0) |
| 2003 | `lote-corrompido_….zip` | ERRO | ✅ ERRO | 0 – ZIP inválido |
| 2004 | `lote-com-arquivos-nao-processaveis_….zip` | CONCLUIDO | ✅ CONCLUIDO | 6 (3 armazenados / 0 / 3) |
| 2005 | `lote-com-erros_….zip` | CONCLUIDO_COM_ERROS | ✅ CONCLUIDO_COM_ERROS | 10 (5 / 4 / 1) |
| 2006 | `lote-valido_….zip` | CONCLUIDO | ✅ CONCLUIDO | 7 (7 / 0 / 0) |

## Evidências

| # | Evidência | O que comprova | Arquivo |
|---|---|---|---|
| 01 | Lista de lotes | Status final de cada cenário | [01-lista-de-lotes.png](01-lista-de-lotes.png) |
| 02 | Upload | Envio do ZIP; API responde 202 e o processamento é assíncrono | [02-upload.png](02-upload.png) |
| 03 | Detalhe do lote válido (#2006) | Classificação pelo conteúdo, fila, status, tentativas, tempo e download | [03-detalhe-lote-valido.png](03-detalhe-lote-valido.png) |
| 04 | Detalhe do lote com erros (#2005) | Falha isolada por arquivo, motivo de cada erro, ignorado e nome duplicado | [04-detalhe-lote-com-erros.png](04-detalhe-lote-com-erros.png) |
| 05 | Dashboard | Arquivos por extensão, tipo e status; tempos médios; lotes por situação | [05-dashboard.png](05-dashboard.png) |
| 06 | RabbitMQ – filas | 18 filas duráveis (principal, retry e DLQ por tipo) | [06-rabbitmq-filas.png](06-rabbitmq-filas.png) |
| 07 | RabbitMQ – visão geral | 6 consumidores (um por worker), nenhuma mensagem pendente | [07-rabbitmq-visao-geral.png](07-rabbitmq-visao-geral.png) |
| 08 | Swagger | Endpoints da API | [08-swagger-endpoints.png](08-swagger-endpoints.png) |
| 09 | Storage | ZIP original e extraídos em `/storage/lotes/{loteId}/` | [09-storage-volume-docker.png](09-storage-volume-docker.png) |
| 10 | Logs de processamento | Logs mínimos da seção 10 com loteId, arquivoId, fila e worker | [2002](logs-lote-2002.txt) · [2003](logs-lote-2003.txt) · [2004](logs-lote-2004.txt) · [2005](logs-lote-2005.txt) · [2006](logs-lote-2006.txt) |
| 11 | Persistência no SQL Server | Tabelas `lote` e `arquivo`: status, tipo, fila, tentativas, erro e resultado | [lotes](evidencia_%20lotes.xlsx) · [arquivos](evidencia_arquivos_lote.xlsx) |

### Logs mínimos (seção 10) – exemplos do lote 2005

| Log | Linha registrada |
|---|---|
| Recebimento do lote | `Lote recebido loteId=2005 nome=lote-com-erros_….zip bytes=3076` |
| Início e fim da extração | `Início da extração loteId=2005` · `Fim da extração loteId=2005 arquivos=10` |
| Arquivo identificado e classificado | `Arquivo identificado loteId=2005 arquivoId=3014 arquivo=clientes_….csv extensao=csv status=PENDENTE fila=queue.csv tipo=DOCUMENTO_CLIENTE` |
| Persistência e publicação na fila | `Lote publicado loteId=2005 fila=queue.lotes` · `Arquivo publicado loteId=2005 arquivoId=3014 fila=queue.csv` |
| Início e fim do processamento | `Início do processamento loteId=2005 arquivoId=3014 tentativa=1` · `Fim do processamento … status=PROCESSADO` |
| Erros | `Erro permanente, sem retry fila=queue.json … motivo=JSON inválido` · `Falha definitiva na ingestão loteId=2003 motivo=Arquivo ZIP corrompido ou inválido` |
| Tentativas de reprocessamento | Não ocorreu nesta rodada (só com falha transitória — parar o `sqlserver` durante um envio gera `Falha transitória, agendando retry`) |

> A captura do dashboard (05) e a exportação do banco (11) são de antes da rodada final (lotes 1 a 1003); o lote 4 da exportação é o mesmo cenário do lote 2005.
