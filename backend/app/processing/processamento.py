"""Caso de uso: processar um arquivo (o que os workers csv/json/xml/txt/storage executam).

Para cada mensagem {"arquivoId", "loteId", "caminho", "tipo", "tentativa"}:
  1. ignora se o arquivo já tem status final (mensagem repetida)
  2. PROCESSANDO
  3. roda o processador do tipo
  4. PROCESSADO / ARMAZENADO com o resultado, ou ERRO com o motivo
  5. tenta fechar o lote (só o último arquivo consegue)
"""
import json
import logging
from pathlib import Path

from app.domain.errors import ErroPermanente
from app.infrastructure.repositories import ArquivoRepository, LoteRepository

log = logging.getLogger(__name__)


class ProcessamentoDeArquivo:
    def __init__(self, processador, session_factory, storage_raiz: str):
        self.processador = processador
        self.session_factory = session_factory
        self.storage_raiz = Path(storage_raiz).resolve()

    def processar(self, mensagem: dict, publisher) -> None:
        arquivo_id = int(mensagem["arquivoId"])
        lote_id = int(mensagem["loteId"])

        with self.session_factory() as session:
            repo = ArquivoRepository(session)
            if repo.obter(arquivo_id) is None:
                raise ErroPermanente(f"Arquivo {arquivo_id} não existe")
            if not repo.iniciar(arquivo_id, int(mensagem.get("tentativa", 1))):
                log.info("Arquivo já finalizado, ignorando mensagem arquivoId=%s", arquivo_id)
                return
            session.commit()

        caminho = self._caminho_confiavel(mensagem["caminho"])
        resultado = self.processador.processar(caminho)  # ErroPermanente -> falhou()
        if mensagem.get("tipo"):
            resultado["tipoDocumental"] = mensagem["tipo"]

        with self.session_factory() as session:
            ArquivoRepository(session).concluir(
                arquivo_id, self.processador.status_sucesso, json.dumps(resultado, ensure_ascii=False))
            session.commit()
        log.info("Arquivo processado loteId=%s arquivoId=%s status=%s",
                 lote_id, arquivo_id, self.processador.status_sucesso)
        self._finalizar_lote(lote_id)

    def falhou(self, mensagem: dict, motivo: str) -> None:
        arquivo_id = int(mensagem.get("arquivoId", 0))
        lote_id = int(mensagem.get("loteId", 0))
        log.warning("Arquivo com erro loteId=%s arquivoId=%s motivo=%s", lote_id, arquivo_id, motivo)
        with self.session_factory() as session:
            ArquivoRepository(session).marcar_erro(arquivo_id, motivo)
            session.commit()
        self._finalizar_lote(lote_id)

    def _finalizar_lote(self, lote_id: int) -> None:
        # transação separada: o status deste arquivo já está gravado
        with self.session_factory() as session:
            if LoteRepository(session).tentar_finalizar(lote_id):
                log.info("Lote finalizado loteId=%s", lote_id)
            session.commit()

    def _caminho_confiavel(self, caminho: str) -> Path:
        p = Path(caminho).resolve()
        if not p.is_relative_to(self.storage_raiz) or not p.is_file():
            raise ErroPermanente(f"Arquivo não encontrado no storage: {caminho}")
        return p
