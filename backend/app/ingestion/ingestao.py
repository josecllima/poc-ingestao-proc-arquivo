"""Caso de uso: ingestão de um lote (o que o worker-ingestao executa).

Fluxo para uma mensagem {"loteId", "caminho"} da queue.lotes:
  1. EXTRAINDO      extrai o ZIP com segurança
  2. CLASSIFICANDO  classifica cada arquivo pelo conteúdo e grava no banco
  3. PROCESSANDO    publica cada arquivo na fila do seu tipo
Arquivos sem fila (extensão desconhecida, vazios, não extraídos) ficam
IGNORADO ou ERRO e não travam o lote.
"""
import logging
from pathlib import Path

from app.classifiers.registry import RegistroDeClassificadores
from app.domain import tipos
from app.domain.errors import ErroPermanente
from app.domain.status import StatusArquivo, StatusLote
from app.infrastructure.models import ArquivoModel
from app.infrastructure.repositories import ArquivoRepository, LoteRepository
from app.infrastructure.topology import fila
from app.ingestion.extracao import ArquivoExtraido, ExtratorZip

log = logging.getLogger(__name__)

STATUS_FINAIS = {StatusLote.CONCLUIDO, StatusLote.CONCLUIDO_COM_ERROS, StatusLote.ERRO}


class IngestaoDeLote:
    def __init__(self, session_factory, extrator: ExtratorZip,
                 classificadores: RegistroDeClassificadores, storage_raiz: str):
        self.session_factory = session_factory
        self.extrator = extrator
        self.classificadores = classificadores
        self.storage_raiz = Path(storage_raiz).resolve()

    # chamado pelo consumidor para cada mensagem
    def processar(self, mensagem: dict, publisher) -> None:
        lote_id = int(mensagem["loteId"])
        zip_path = self._caminho_confiavel(mensagem["caminho"])

        with self.session_factory() as session:
            lote = LoteRepository(session).obter(lote_id)
            if lote is None:
                raise ErroPermanente(f"Lote {lote_id} não existe")
            if lote.status in STATUS_FINAIS:
                # mensagem repetida: o RabbitMQ entrega "pelo menos uma vez"
                log.info("Lote já finalizado, ignorando mensagem loteId=%s status=%s", lote_id, lote.status)
                return
            status_atual = lote.status
            ja_registrados = ArquivoRepository(session).listar_do_lote(lote_id)

        if status_atual == StatusLote.PROCESSANDO:
            # tentativa anterior caiu depois de gravar os arquivos: só publica os pendentes
            log.info("Retomando lote loteId=%s arquivos=%s", lote_id, len(ja_registrados))
            self._publicar(lote_id, ja_registrados, publisher)
            return

        self._mudar_status(lote_id, StatusLote.EXTRAINDO)
        log.info("Início da extração loteId=%s zip=%s", lote_id, zip_path.name)
        destino = zip_path.parent / "extraidos"
        self.extrator.limpar(destino)  # descarta restos de uma tentativa interrompida
        extraidos = self.extrator.extrair(zip_path, destino)
        log.info("Fim da extração loteId=%s arquivos=%s", lote_id, len(extraidos))

        self._mudar_status(lote_id, StatusLote.CLASSIFICANDO)
        with self.session_factory() as session:
            repo = ArquivoRepository(session)
            registros = [repo.adicionar(self._registro(lote_id, item)) for item in extraidos]
            session.flush()  # gera os ids para o log abaixo
            for a in registros:
                log.info("Arquivo identificado loteId=%s arquivoId=%s arquivo=%s extensao=%s status=%s fila=%s tipo=%s%s",
                         lote_id, a.id, a.caminho_relativo, a.extensao, a.status, a.fila, a.tipo_documental,
                         f" motivo={a.erro}" if a.erro else "")
            lote_repo = LoteRepository(session)
            lote_repo.definir_total(lote_id, len(registros))
            lote_repo.atualizar_status(lote_id, StatusLote.PROCESSANDO)
            session.commit()  # grava tudo de uma vez, já com os ids gerados

        self._publicar(lote_id, registros, publisher)

    # chamado pelo consumidor quando a falha é definitiva
    def falhou(self, mensagem: dict, motivo: str) -> None:
        lote_id = int(mensagem.get("loteId", 0))
        log.error("Falha definitiva na ingestão loteId=%s motivo=%s", lote_id, motivo)
        with self.session_factory() as session:
            LoteRepository(session).atualizar_status(lote_id, StatusLote.ERRO, motivo)
            session.commit()

    def _registro(self, lote_id: int, item: ArquivoExtraido) -> ArquivoModel:
        arquivo = ArquivoModel(
            lote_id=lote_id, nome=item.nome[:255], caminho_relativo=item.caminho_relativo[:500],
            caminho_storage=str(item.caminho) if item.caminho else None,
            extensao=item.extensao[:20] or None, tamanho_bytes=item.tamanho,
        )
        destino = tipos.fila_para(item.extensao)

        if item.erro:
            arquivo.status, arquivo.erro = StatusArquivo.ERRO, item.erro
        elif destino is None:
            arquivo.status = StatusArquivo.IGNORADO
            arquivo.erro = f"Extensão não suportada: .{item.extensao}" if item.extensao else "Arquivo sem extensão"
        elif item.tamanho == 0:
            arquivo.status, arquivo.erro = StatusArquivo.IGNORADO, "Arquivo vazio"
        else:
            arquivo.status = StatusArquivo.PENDENTE
            arquivo.fila = fila(destino)
            if item.extensao in tipos.EXTENSOES_PROCESSAVEIS:
                arquivo.tipo_documental = self.classificadores.classificar(item.extensao, item.caminho)
        return arquivo

    def _publicar(self, lote_id: int, arquivos: list[ArquivoModel], publisher) -> None:
        pendentes = [a for a in arquivos if a.status == StatusArquivo.PENDENTE]
        for arquivo in pendentes:
            publisher.publicar(arquivo.fila.removeprefix("queue."), {
                "arquivoId": arquivo.id, "loteId": lote_id, "caminho": arquivo.caminho_storage,
                "tipo": arquivo.tipo_documental, "tentativa": 1,
            })
            with self.session_factory() as session:
                ArquivoRepository(session).marcar_publicado(arquivo.id)
                session.commit()
            log.info("Arquivo publicado loteId=%s arquivoId=%s fila=%s tipo=%s",
                     lote_id, arquivo.id, arquivo.fila, arquivo.tipo_documental)

        # lote sem nada para processar (tudo ignorado) já fecha aqui
        with self.session_factory() as session:
            if LoteRepository(session).tentar_finalizar(lote_id):
                log.info("Lote finalizado na ingestão loteId=%s", lote_id)
            session.commit()

    def _mudar_status(self, lote_id: int, status: StatusLote) -> None:
        with self.session_factory() as session:
            LoteRepository(session).atualizar_status(lote_id, status)
            session.commit()

    def _caminho_confiavel(self, caminho: str) -> Path:
        """Só aceita caminhos dentro do /storage (a mensagem não é confiável por si)."""
        p = Path(caminho).resolve()
        if not p.is_relative_to(self.storage_raiz) or not p.is_file():
            raise ErroPermanente(f"Caminho do ZIP inválido ou inexistente: {caminho}")
        return p
