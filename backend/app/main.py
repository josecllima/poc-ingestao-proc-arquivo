import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import health, lotes
from app.domain.errors import ErroDeValidacao, FilaIndisponivel, LimiteExcedido
from app.infrastructure.messaging import preparar_topologia

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# Tradução de erro de negócio para código HTTP
ERROS_HTTP = {ErroDeValidacao: 400, LimiteExcedido: 413, FilaIndisponivel: 503}


@asynccontextmanager
async def lifespan(app: FastAPI):
    preparar_topologia()  # roda uma vez, quando a API sobe
    yield


app = FastAPI(title="POC Ingestão e Processamento de Arquivos", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(lotes.router)


@app.exception_handler(ErroDeValidacao)
@app.exception_handler(LimiteExcedido)
@app.exception_handler(FilaIndisponivel)
async def erro_de_negocio(request: Request, exc: Exception):
    return JSONResponse(status_code=ERROS_HTTP[type(exc)], content={"detail": str(exc)})


logging.getLogger("pika").setLevel(logging.WARNING)
