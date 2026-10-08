"""Gravação de arquivos no volume /storage.

O upload é lido em pedaços de 1 MB: calcula o hash e para assim que
passa do limite, sem nunca carregar o ZIP inteiro na memória.
"""
import hashlib
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from app.domain.errors import LimiteExcedido

CHUNK = 1024 * 1024  # 1 MB


class LocalStorage:
    def __init__(self, raiz: str):
        self.raiz = Path(raiz)
        (self.raiz / "tmp").mkdir(parents=True, exist_ok=True)

    def receber_upload(self, origem: BinaryIO, limite_bytes: int) -> tuple[Path, int, str]:
        """Grava numa pasta temporária. Retorna (caminho, tamanho, sha256)."""
        destino = self.raiz / "tmp" / f"{uuid.uuid4().hex}.zip"
        sha, total = hashlib.sha256(), 0
        try:
            with destino.open("wb") as f:
                while chunk := origem.read(CHUNK):
                    total += len(chunk)
                    if total > limite_bytes:
                        raise LimiteExcedido(f"O ZIP excede o limite de {limite_bytes // CHUNK} MB")
                    sha.update(chunk)
                    f.write(chunk)
        except Exception:
            destino.unlink(missing_ok=True)  # não deixa lixo se der erro
            raise
        return destino, total, sha.hexdigest()

    def mover_para_lote(self, temporario: Path, lote_id: int, nome: str) -> Path:
        pasta = self.raiz / "lotes" / str(lote_id)
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / nome
        shutil.move(temporario, destino)
        return destino

    def descartar(self, caminho: Path) -> None:
        caminho.unlink(missing_ok=True)
