"""Política de retenção: apaga do storage os arquivos de lotes antigos já finalizados.

Uso (dentro de qualquer container da aplicação):
    docker compose exec backend python -m app.manutencao.retencao            # usa RETENCAO_DIAS
    docker compose exec backend python -m app.manutencao.retencao --dias 7
    docker compose exec backend python -m app.manutencao.retencao --simular  # só lista

Regras:
  - só lotes com status final (CONCLUIDO, CONCLUIDO_COM_ERROS, ERRO) e
    concluídos/recebidos há mais de N dias; lotes em andamento nunca são tocados
  - apaga a pasta /storage/lotes/<id> (ZIP original + extraídos)
  - o banco é mantido (histórico e resultados); o download passa a responder 404
Em produção, rodaria agendado (cron, CronJob do Kubernetes etc.).
"""
import argparse
import logging
import shutil
from datetime import timedelta
from pathlib import Path

from sqlalchemy import or_, select

from app.config import settings
from app.domain.status import StatusLote
from app.infrastructure.db import SessionLocal
from app.infrastructure.models import LoteModel, agora_utc

log = logging.getLogger(__name__)

STATUS_FINAIS = (StatusLote.CONCLUIDO, StatusLote.CONCLUIDO_COM_ERROS, StatusLote.ERRO)


def lotes_expirados(session, dias: int) -> list[int]:
    limite = agora_utc() - timedelta(days=dias)
    consulta = select(LoteModel.id).where(
        LoteModel.status.in_(STATUS_FINAIS),
        or_(LoteModel.concluido_em < limite,
            (LoteModel.concluido_em.is_(None)) & (LoteModel.recebido_em < limite)),
    )
    return list(session.scalars(consulta))


def aplicar_retencao(dias: int, storage_raiz: str, simular: bool = False) -> list[int]:
    raiz = Path(storage_raiz) / "lotes"
    with SessionLocal() as session:
        ids = lotes_expirados(session, dias)

    apagados = []
    for lote_id in ids:
        pasta = raiz / str(lote_id)
        if not pasta.exists():
            continue
        if simular:
            log.info("[simulação] apagaria loteId=%s pasta=%s", lote_id, pasta)
        else:
            shutil.rmtree(pasta, ignore_errors=True)
            log.info("Retenção: arquivos removidos loteId=%s pasta=%s", lote_id, pasta)
        apagados.append(lote_id)

    log.info("Retenção concluída dias=%s lotes=%s simulacao=%s", dias, len(apagados), simular)
    return apagados


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Remove do storage os arquivos de lotes antigos")
    parser.add_argument("--dias", type=int, default=settings.retencao_dias)
    parser.add_argument("--simular", action="store_true", help="só lista, não apaga")
    args = parser.parse_args()
    aplicar_retencao(args.dias, settings.storage_path, args.simular)


if __name__ == "__main__":
    main()
