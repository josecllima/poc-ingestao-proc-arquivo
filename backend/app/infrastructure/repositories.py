"""Acesso a dados (padrão Repository).

Toda consulta ou gravação de lote passa por aqui. O resto do código não
escreve SQL nem conhece detalhes do SQLAlchemy.
"""
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.domain.status import StatusArquivo, StatusLote
from app.infrastructure.models import ArquivoModel, LoteModel, agora_utc


class LoteRepository:
    def __init__(self, session: Session):
        self.session = session

    def criar(self, nome_zip: str, hash_sha256: str) -> LoteModel:
        lote = LoteModel(nome_zip=nome_zip, hash_sha256=hash_sha256, status=StatusLote.RECEBIDO)
        self.session.add(lote)
        self.session.flush()  # envia o INSERT para o banco e preenche o id gerado
        return lote

    def obter(self, lote_id: int) -> LoteModel | None:
        return self.session.get(LoteModel, lote_id)

    def obter_por_hash(self, hash_sha256: str) -> LoteModel | None:
        return self.session.scalar(select(LoteModel).where(LoteModel.hash_sha256 == hash_sha256))

    def atualizar_status(self, lote_id: int, status: StatusLote, mensagem_erro: str | None = None) -> None:
        lote = self.session.get(LoteModel, lote_id)
        if lote is None:
            return
        lote.status = status
        if mensagem_erro:
            lote.mensagem_erro = mensagem_erro[:1000]

    def definir_total(self, lote_id: int, total: int) -> None:
        lote = self.session.get(LoteModel, lote_id)
        if lote is not None:
            lote.total_arquivos = total

    def tentar_finalizar(self, lote_id: int) -> bool:
        """Fecha o lote se nenhum arquivo estiver pendente.

        Um único UPDATE atômico: com vários workers terminando ao mesmo
        tempo, só o último consegue mudar o status. Retorna True se fechou.
        """
        resultado = self.session.execute(text("""
            UPDATE lote
               SET status = CASE WHEN EXISTS (SELECT 1 FROM arquivo
                                               WHERE lote_id = :id AND status = :erro)
                                 THEN :com_erros ELSE :concluido END,
                   concluido_em = SYSUTCDATETIME()
             WHERE id = :id
               AND status = :processando
               AND NOT EXISTS (SELECT 1 FROM arquivo
                                WHERE lote_id = :id
                                  AND status IN (:pendente, :publicado, :processando_arq))
        """), {
            "id": lote_id,
            "erro": StatusArquivo.ERRO,
            "com_erros": StatusLote.CONCLUIDO_COM_ERROS,
            "concluido": StatusLote.CONCLUIDO,
            "processando": StatusLote.PROCESSANDO,
            "pendente": StatusArquivo.PENDENTE,
            "publicado": StatusArquivo.PUBLICADO,
            "processando_arq": StatusArquivo.PROCESSANDO,
        })
        return resultado.rowcount == 1


class ArquivoRepository:
    def __init__(self, session: Session):
        self.session = session

    def adicionar(self, arquivo: ArquivoModel) -> ArquivoModel:
        self.session.add(arquivo)
        return arquivo

    def listar_do_lote(self, lote_id: int) -> list[ArquivoModel]:
        return list(self.session.scalars(
            select(ArquivoModel).where(ArquivoModel.lote_id == lote_id).order_by(ArquivoModel.id)))

    def marcar_publicado(self, arquivo_id: int) -> None:
        # só muda se ainda estiver PENDENTE: o worker do tipo pode ter terminado antes
        self.session.execute(
            update(ArquivoModel)
            .where(ArquivoModel.id == arquivo_id, ArquivoModel.status == StatusArquivo.PENDENTE)
            .values(status=StatusArquivo.PUBLICADO))

    def obter(self, arquivo_id: int) -> ArquivoModel | None:
        return self.session.get(ArquivoModel, arquivo_id)

    def iniciar(self, arquivo_id: int, tentativa: int) -> bool:
        """Marca PROCESSANDO. Retorna False se o arquivo já tem status final."""
        resultado = self.session.execute(
            update(ArquivoModel)
            .where(ArquivoModel.id == arquivo_id,
                   ArquivoModel.status.in_([StatusArquivo.PENDENTE, StatusArquivo.PUBLICADO,
                                            StatusArquivo.PROCESSANDO]))
            .values(status=StatusArquivo.PROCESSANDO, tentativas=tentativa, iniciado_em=agora_utc()))
        return resultado.rowcount == 1

    def concluir(self, arquivo_id: int, status: StatusArquivo, resultado_json: str) -> None:
        self.session.execute(
            update(ArquivoModel).where(ArquivoModel.id == arquivo_id)
            .values(status=status, resultado=resultado_json, erro=None, finalizado_em=agora_utc()))

    def marcar_erro(self, arquivo_id: int, erro: str) -> None:
        self.session.execute(
            update(ArquivoModel).where(ArquivoModel.id == arquivo_id)
            .values(status=StatusArquivo.ERRO, erro=erro[:1000], finalizado_em=agora_utc()))
