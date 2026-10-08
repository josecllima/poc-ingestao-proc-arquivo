"""Endpoints de lotes."""
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.infrastructure.db import SessionLocal
from app.infrastructure.messaging import RabbitPublisher
from app.infrastructure.repositories import LoteRepository
from app.infrastructure.storage import LocalStorage
from app.ingestion.recebimento import RecebimentoDeLote

router = APIRouter(prefix="/lotes", tags=["lotes"])


class LoteResposta(BaseModel):
    loteId: int
    nomeZip: str
    status: str
    recebidoEm: datetime
    duplicado: bool = False


def _resposta(lote, duplicado: bool = False) -> LoteResposta:
    return LoteResposta(loteId=lote.id, nomeZip=lote.nome_zip, status=lote.status,
                        recebidoEm=lote.recebido_em, duplicado=duplicado)


def get_recebimento() -> RecebimentoDeLote:
    """Monta o caso de uso com as dependências reais (como o container de DI do .NET)."""
    return RecebimentoDeLote(
        storage=LocalStorage(settings.storage_path),
        publisher=RabbitPublisher(),
        session_factory=SessionLocal,
        limite_bytes=settings.max_zip_mb * 1024 * 1024,
    )


@router.post("", status_code=202, response_model=LoteResposta)
def enviar_lote(response: Response, arquivo: UploadFile = File(...),
                servico: RecebimentoDeLote = Depends(get_recebimento)):
    lote, duplicado = servico.receber(arquivo.filename, arquivo.file)
    if duplicado:
        response.status_code = 200
    return _resposta(lote, duplicado)


@router.get("/{lote_id}", response_model=LoteResposta)
def obter_lote(lote_id: int):
    with SessionLocal() as session:
        lote = LoteRepository(session).obter(lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    return _resposta(lote)
