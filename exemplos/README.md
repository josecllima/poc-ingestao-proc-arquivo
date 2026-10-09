# Arquivos de teste

Pasta equivalente à `samples/` pedida no enunciado. Todos os dados são fictícios. Comandos (na raiz do projeto):

| Comando | Atalho no Windows | Gera |
|---|---|---|
| `python exemplos/gerar_exemplos.py` | `3_gerar_documentos.bat` | Os ZIPs oficiais abaixo, em `exemplos/`, com nomes fixos |
| `python exemplos/gerar_exemplos.py --carimbo` | `4_gerar_documentos_outros.bat` | Lotes **inéditos** em `exemplos/gerados/`: o ZIP e cada arquivo interno ganham o sufixo `_ddmmaaaahhmmss` e os dados mudam a cada execução |

Com `--carimbo` dá para enviar o mesmo cenário várias vezes sem cair na regra de duplicidade (hash do ZIP). Para testar a duplicidade, reenvie um ZIP já enviado — mesmo renomeado, ele é reconhecido como duplicado. A pasta `exemplos/gerados/` não vai para o Git.

| ZIP | Para demonstrar | Status final do lote |
|---|---|---|
| `lote-valido.zip` | Um arquivo válido de cada tipo e a classificação documental | CONCLUIDO |
| `lote-com-erros.zip` | Arquivos inválidos, vazio, nome duplicado e path traversal, sem travar o lote | CONCLUIDO_COM_ERROS |
| `lote-com-arquivos-nao-processaveis.zip` | PDF e imagens armazenados; extensões desconhecidas ignoradas | CONCLUIDO |
| `lote-corrompido.zip` | ZIP inválido | ERRO |
| `lote-1mb.zip` | Volume: cerca de 1 MB por arquivo | CONCLUIDO |

## lote-valido.zip

| Arquivo | Status | Tipo documental |
|---|---|---|
| clientes.csv | PROCESSADO | DOCUMENTO_CLIENTE |
| clientes.xml | PROCESSADO | DOCUMENTO_CLIENTE |
| movimentos.xml | PROCESSADO | DOCUMENTO_MOVIMENTO |
| movimentos.txt | PROCESSADO | DOCUMENTO_MOVIMENTO |
| produtos.json | PROCESSADO | DOCUMENTO_PRODUTO |
| documentos/comprovante.pdf | ARMAZENADO | – |
| imagens/logo.png | ARMAZENADO | – |

## lote-com-erros.zip

| Arquivo | Status | Motivo |
|---|---|---|
| clientes.csv | PROCESSADO | Válido (controle) |
| csv-colunas-faltando.csv | ERRO | Linha 3 tem 2 colunas; o cabeçalho tem 3 |
| json-quebrado.json | ERRO | JSON inválido |
| xml-malformado.xml | ERRO | XML malformado (tag fechada errada) |
| pedidos.xml | PROCESSADO | Válido, raiz sem regra: TIPO_DESCONHECIDO |
| lista.json | PROCESSADO | Válido (lista), sem regra: TIPO_DESCONHECIDO |
| vazio.txt | IGNORADO | Arquivo vazio |
| dados/relatorio.txt | PROCESSADO | Válido |
| DADOS/relatorio.txt | PROCESSADO | Nome duplicado: gravado como `DADOS/relatorio_1.txt` |
| ../fora-do-lote.txt | ERRO | Caminho inseguro: não é gravado fora da pasta do lote |

## lote-com-arquivos-nao-processaveis.zip

| Arquivo | Status | Motivo |
|---|---|---|
| documentos/contrato.pdf | ARMAZENADO | Só metadados |
| imagens/foto.jpg | ARMAZENADO | Só metadados |
| imagens/grafico.png | ARMAZENADO | Só metadados |
| planilha.xlsx | IGNORADO | Extensão não suportada |
| instalador.exe | IGNORADO | Extensão não suportada |
| LEIAME | IGNORADO | Arquivo sem extensão |
