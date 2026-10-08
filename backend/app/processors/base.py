"""Contrato dos processadores (um por tipo de arquivo, padrão Strategy)."""
from pathlib import Path
from typing import Protocol

from app.domain.errors import ErroPermanente
from app.domain.status import StatusArquivo


class Processador(Protocol):
    # status gravado quando dá certo: PROCESSADO ou ARMAZENADO
    status_sucesso: StatusArquivo

    def processar(self, caminho: Path) -> dict:
        """Lê o arquivo e devolve o resultado (vira JSON na coluna resultado).

        Conteúdo inválido -> lança ErroPermanente (status ERRO, sem retry).
        """
        ...


def ler_texto(caminho: Path) -> str:
    """Lê como UTF-8 (com ou sem BOM); se falhar, tenta Latin-1."""
    dados = caminho.read_bytes()
    if b"\x00" in dados[:8192]:
        raise ErroPermanente("O arquivo parece binário, não é texto")
    try:
        return dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dados.decode("latin-1")
