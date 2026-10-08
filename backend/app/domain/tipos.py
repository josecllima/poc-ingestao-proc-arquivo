"""Tipos documentais e o roteamento de extensão para fila."""

DOCUMENTO_CLIENTE = "DOCUMENTO_CLIENTE"
DOCUMENTO_MOVIMENTO = "DOCUMENTO_MOVIMENTO"
DOCUMENTO_PRODUTO = "DOCUMENTO_PRODUTO"
TIPO_DESCONHECIDO = "TIPO_DESCONHECIDO"

# extensão -> fila (sem o prefixo "queue.")
FILA_POR_EXTENSAO = {
    "csv": "csv",
    "json": "json",
    "xml": "xml",
    "txt": "txt",
    "pdf": "storage",
    "jpg": "storage",
    "jpeg": "storage",
    "png": "storage",
}

# só estes têm o conteúdo analisado; o resto vai direto para o storage
EXTENSOES_PROCESSAVEIS = {"csv", "json", "xml", "txt"}


def fila_para(extensao: str) -> str | None:
    """Retorna a fila do tipo ou None se a extensão não é reconhecida."""
    return FILA_POR_EXTENSAO.get(extensao)
