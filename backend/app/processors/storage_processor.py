"""Seção 5.5: PDF e imagens não têm o conteúdo lido, só os metadados."""
import hashlib
import mimetypes

from app.domain.status import StatusArquivo


class StorageProcessor:
    status_sucesso = StatusArquivo.ARMAZENADO

    def processar(self, caminho):
        sha = hashlib.sha256()
        with caminho.open("rb") as f:
            while bloco := f.read(1024 * 1024):
                sha.update(bloco)
        return {
            "tamanhoBytes": caminho.stat().st_size,
            "tipoMime": mimetypes.guess_type(caminho.name)[0] or "application/octet-stream",
            "sha256": sha.hexdigest(),
            "caminhoArmazenado": str(caminho),
        }
