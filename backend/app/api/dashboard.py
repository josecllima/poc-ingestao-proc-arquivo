"""Endpoint do dashboard."""
from fastapi import APIRouter

from app.infrastructure import consultas
from app.infrastructure.db import SessionLocal

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", summary="Arquivos por extensão, tipo e status; tempos médios; lotes por situação")
def dashboard():
    with SessionLocal() as session:
        return consultas.dashboard(session)
