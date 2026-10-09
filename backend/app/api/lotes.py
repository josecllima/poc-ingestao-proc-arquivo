"""Endpoints de lotes: envio, lista e detalhes."""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.domain.status import StatusLote
from app.infrastructure import consultas
from app.infrastructure.db import SessionLocal
from app.infrastructure.messaging import RabbitPublisher
from app.infrastructure.repositories import ArquivoRepository
from app.infrastructure.storage import LocalStorage
from app.ingestion.recebimento import RecebimentoDeLote

router = APIRouter(prefix="/lotes", tags=["lotes"])

STATUS_FINAIS = {StatusLote.CONCLUIDO, StatusLote.CONCLUIDO_COM_ERROS, StatusLote.ERRO}


class LoteResposta(BaseModel):
    loteId: int
    nomeZip: str
    status: str
    recebidoEm: datetime
    duplicado: bool = False


def get_recebimento() -> RecebimentoDeLote:
    """Monta o caso de uso com as dependências reais (como o container de DI do .NET)."""
    return RecebimentoDeLote(
        storage=LocalStorage(settings.storage_path),
        publisher=RabbitPublisher(),
        session_factory=SessionLocal,
        limite_bytes=settings.max_zip_mb * 1024 * 1024,
    )


@router.post("", status_code=202, response_model=LoteResposta,
             summary="Envia um ZIP para processamento assíncrono")
def enviar_lote(response: Response, arquivo: UploadFile = File(...),
                servico: RecebimentoDeLote = Depends(get_recebimento)):
    lote, duplicado = servico.receber(arquivo.filename, arquivo.file)
    if duplicado:
        response.status_code = 200
    return LoteResposta(loteId=lote.id, nomeZip=lote.nome_zip, status=lote.status,
                        recebidoEm=lote.recebido_em, duplicado=duplicado)


@router.get("", summary="Lista os lotes (mais recentes primeiro), com paginação e filtro por status")
def listar_lotes(pagina: int = Query(1, ge=1), tamanho: int = Query(20, ge=1, le=100),
                 status: StatusLote | None = None):
    with SessionLocal() as session:
        return consultas.listar_lotes(session, pagina, tamanho, status.value if status else None)


@router.get("/{lote_id}", summary="Detalhes do lote: progresso, contagens e todos os arquivos")
def obter_lote(lote_id: int):
    with SessionLocal() as session:
        resumo = consultas.resumo_do_lote(session, lote_id)
        if resumo is None:
            raise HTTPException(status_code=404, detail="Lote não encontrado")
        arquivos = ArquivoRepository(session).listar_do_lote(lote_id)

    quantidades = consultas.quantidades(resumo)
    total = quantidades["total"]
    finalizados = total - quantidades["pendentes"]
    if resumo.status in STATUS_FINAIS:
        progresso = 100.0
    else:
        progresso = round(finalizados / total * 100, 1) if total else 0.0

    return {
        "loteId": resumo.id,
        "nomeZip": resumo.nome_zip,
        "status": resumo.status,
        "erro": resumo.mensagem_erro,
        "recebidoEm": resumo.recebido_em,
        "concluidoEm": resumo.concluido_em,
        "progresso": progresso,
        "quantidades": quantidades,
        "arquivos": [_arquivo(a) for a in arquivos],
    }


def _arquivo(a) -> dict:
    tempo_ms = None
    if a.iniciado_em and a.finalizado_em:
        tempo_ms = round((a.finalizado_em - a.iniciado_em).total_seconds() * 1000, 1)
    return {
        "arquivoId": a.id,
        "nome": a.nome,
        "caminhoRelativo": a.caminho_relativo,
        "extensao": a.extensao,
        "tamanhoBytes": a.tamanho_bytes,
        "tipoDocumental": a.tipo_documental,
        "fila": a.fila,
        "status": a.status,
        "tentativas": a.tentativas,
        "tempoMs": tempo_ms,
        "erro": a.erro,
        "resultado": json.loads(a.resultado) if a.resultado else None,
    }
