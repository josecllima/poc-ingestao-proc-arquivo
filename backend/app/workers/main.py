"""Ponto de entrada de todos os workers (padrão Factory).

Uso: python -m app.workers.main --fila lotes

A mesma imagem Docker roda qualquer worker; muda só o --fila.
"""
import argparse
import logging

from app.classifiers.registry import RegistroDeClassificadores
from app.config import settings
from app.infrastructure.db import SessionLocal
from app.ingestion.extracao import ExtratorZip
from app.ingestion.ingestao import IngestaoDeLote
from app.workers.consumidor import Consumidor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logging.getLogger("pika").setLevel(logging.WARNING)


def criar_ingestao():
    return IngestaoDeLote(
        session_factory=SessionLocal,
        extrator=ExtratorZip(settings.max_arquivos_por_lote, settings.max_descompactado_mb * 1024 * 1024),
        classificadores=RegistroDeClassificadores(),
        storage_raiz=settings.storage_path,
    )


# fila -> função que monta o handler. Os workers por tipo entram aqui no passo 5.
HANDLERS = {
    "lotes": criar_ingestao,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker de processamento")
    parser.add_argument("--fila", required=True, choices=sorted(HANDLERS))
    args = parser.parse_args()

    handler = HANDLERS[args.fila]()
    Consumidor(args.fila, handler, settings.max_tentativas).iniciar()


if __name__ == "__main__":
    main()
