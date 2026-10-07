from fastapi import APIRouter, Response, status

from app.infrastructure import db, messaging

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response):
    checks = {}
    for nome, ping in (("sqlserver", db.ping), ("rabbitmq", messaging.ping)):
        try:
            ping()
            checks[nome] = "ok"
        except Exception as exc:
            checks[nome] = f"erro: {type(exc).__name__}"

    saudavel = all(v == "ok" for v in checks.values())
    if not saudavel:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if saudavel else "degradado", "checks": checks}