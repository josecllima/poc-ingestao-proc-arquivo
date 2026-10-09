#!/usr/bin/env bash
# Teste de ponta a ponta usado pelo CI (também roda localmente no Linux/WSL/Git Bash com o ambiente no ar).
# Envia cada ZIP de exemplos/ e confere se o lote termina no status esperado.
set -euo pipefail

API="${API:-http://localhost:8000}"
FRONT="${FRONT:-http://localhost:3000}"

esperar_url() {  # esperar_url <url> <segundos>
  local url=$1 limite=$2 inicio=$SECONDS
  until curl -fs "$url" > /dev/null; do
    if (( SECONDS - inicio > limite )); then echo "❌ $url não respondeu em ${limite}s"; return 1; fi
    sleep 5
  done
  echo "✅ $url no ar"
}

enviar_e_conferir() {  # enviar_e_conferir <zip> <status esperado>
  local zip=$1 esperado=$2 resposta id status inicio=$SECONDS
  resposta=$(curl -fs -F "arquivo=@exemplos/$zip" "$API/lotes")
  id=$(jq -r .loteId <<< "$resposta")
  echo "→ $zip enviado: loteId=$id"
  while true; do
    status=$(curl -fs "$API/lotes/$id" | jq -r .status)
    case "$status" in CONCLUIDO|CONCLUIDO_COM_ERROS|ERRO) break ;; esac
    if (( SECONDS - inicio > 180 )); then echo "❌ lote $id ainda em $status depois de 180s"; return 1; fi
    sleep 2
  done
  if [[ "$status" != "$esperado" ]]; then
    echo "❌ $zip: esperado $esperado, veio $status"
    curl -fs "$API/lotes/$id" | jq '.arquivos[] | {nome, status, erro}'
    return 1
  fi
  echo "✅ $zip → $status ($(curl -fs "$API/lotes/$id" | jq -r '.quantidades | "\(.total) arquivos, \(.erros) erros, \(.ignorados) ignorados"'))"
}

esperar_url "$API/health" 420
esperar_url "$FRONT" 120

enviar_e_conferir lote-valido.zip                          CONCLUIDO
enviar_e_conferir lote-com-erros.zip                       CONCLUIDO_COM_ERROS
enviar_e_conferir lote-com-arquivos-nao-processaveis.zip   CONCLUIDO
enviar_e_conferir lote-corrompido.zip                      ERRO

# idempotência: o mesmo ZIP de novo deve voltar como duplicado (HTTP 200)
codigo=$(curl -s -o /tmp/dup.json -w '%{http_code}' -F "arquivo=@exemplos/lote-valido.zip" "$API/lotes")
[[ "$codigo" == "200" && "$(jq -r .duplicado /tmp/dup.json)" == "true" ]] \
  && echo "✅ reenvio do mesmo ZIP reconhecido como duplicado" \
  || { echo "❌ reenvio: esperado 200 + duplicado=true, veio $codigo $(cat /tmp/dup.json)"; exit 1; }

# dashboard e lista de lotes respondem
curl -fs "$API/dashboard" | jq -e '.lotes.total >= 4' > /dev/null || { echo "❌ /dashboard falhou"; exit 1; }
echo "✅ /dashboard ok"
curl -fs "$API/lotes" | jq -e '.total >= 4' > /dev/null || { echo "❌ /lotes falhou"; exit 1; }
echo "✅ /lotes ok"

echo "🎉 Teste de ponta a ponta concluído"
