"""Caso de uso: receber um lote.

Valida, grava o ZIP, registra o lote e publica na queue.lotes.
Recebe storage, publisher e banco pelo construtor (injeção de
dependência), então os testes podem passar versões falsas.
"""
import logging
from pathlib import Path
from typing import BinaryIO

from app.domain.errors import ErroDeValidacao, FilaIndisponivel
from app.domain.status import StatusLote
from app.infrastructure.models import LoteModel
from app.infrastructure.repositories import LoteRepository

log = logging.getLogger(__name__)

# Mensagem gravada quando o RabbitMQ está fora no momento do upload.
# Um lote com este erro pode ser reenviado: o mesmo ZIP volta para a fila.
ERRO_ENFILEIRAMENTO = "Falha ao enfileirar o lote"


class RecebimentoDeLote:
    def __init__(self, storage, publisher, session_factory, limite_bytes: int):
        self.storage = storage
        self.publisher = publisher
        self.session_factory = session_factory
        self.limite_bytes = limite_bytes

    def receber(self, nome_arquivo: str | None, conteudo: BinaryIO) -> tuple[LoteModel, bool]:
        """Retorna (lote, duplicado)."""
        nome = Path(nome_arquivo or "").name  # descarta qualquer caminho enviado pelo cliente
        if not nome.lower().endswith(".zip"):
            raise ErroDeValidacao("Envie um arquivo .zip")

        temporario, tamanho, sha = self.storage.receber_upload(conteudo, self.limite_bytes)
        if tamanho == 0:
            self.storage.descartar(temporario)
            raise ErroDeValidacao("O arquivo está vazio")

        with self.session_factory() as session:
            repo = LoteRepository(session)
            existente = repo.obter_por_hash(sha)
            if existente and not self._pode_reenfileirar(existente):
                self.storage.descartar(temporario)
                log.info("ZIP repetido, devolvendo lote existente loteId=%s", existente.id)
                return existente, True
            if existente:
                # o envio anterior falhou só porque a fila estava fora: reaproveita o lote
                lote = existente
                lote.status, lote.mensagem_erro = StatusLote.RECEBIDO, None
                log.info("Reenviando lote que falhou ao enfileirar loteId=%s", lote.id)
            else:
                lote = repo.criar(nome, sha)
            session.commit()
            session.refresh(lote)
            session.expunge(lote)

        caminho = self.storage.mover_para_lote(temporario, lote.id, lote.nome_zip)
        log.info("Lote recebido loteId=%s nome=%s bytes=%s", lote.id, lote.nome_zip, tamanho)
        self._enfileirar(lote, caminho)
        return lote, False

    @staticmethod
    def _pode_reenfileirar(lote: LoteModel) -> bool:
        return lote.status == StatusLote.ERRO and lote.mensagem_erro == ERRO_ENFILEIRAMENTO

    def _enfileirar(self, lote: LoteModel, caminho: Path) -> None:
        try:
            self.publisher.publicar("lotes", {"loteId": lote.id, "caminho": str(caminho), "tentativa": 1})
            log.info("Lote publicado loteId=%s fila=queue.lotes", lote.id)
        except Exception as exc:
            log.exception("Falha ao publicar loteId=%s", lote.id)
            with self.session_factory() as session:
                LoteRepository(session).atualizar_status(lote.id, StatusLote.ERRO, ERRO_ENFILEIRAMENTO)
                session.commit()
            lote.status = StatusLote.ERRO
            raise FilaIndisponivel("Fila indisponível, tente novamente em instantes") from exc
