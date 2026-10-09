"""Ponto de entrada de todos os workers (padrão Factory).

Uso: python -m app.workers.main --fila lotes

A mesma imagem Docker roda qualquer worker; muda só o --fila.
"""
import argparse
import logging
import socket

from app.classifiers.registry import RegistroDeClassificadores
from app.config import settings
from app.infrastructure.db import SessionLocal
from app.ingestion.extracao import ExtratorZip
from app.ingestion.ingestao import IngestaoDeLote
from app.processing.processamento import ProcessamentoDeArquivo
from app.processors.registry import PROCESSADORES, criar_processador
from app.workers.consumidor import Consumidor



def configurar_logs(fila: str) -> None:
    """Toda linha de log leva o nome do worker (fila + container), útil com réplicas (--scale)."""
    worker = f"worker-{fila}@{socket.gethostname()}"
    logging.basicConfig(level=logging.INFO,
                        format=f"%(asctime)s %(levelname)s worker={worker} %(name)s %(message)s")
    logging.getLogger("pika").setLevel(logging.WARNING)


def criar_ingestao():
    return IngestaoDeLote(
        session_factory=SessionLocal,
        extrator=ExtratorZip(settings.max_arquivos_por_lote, settings.max_descompactado_mb * 1024 * 1024),
        classificadores=RegistroDeClassificadores(),
        storage_raiz=settings.storage_path,
    )


def criar_processamento(tipo: str):
    return lambda: ProcessamentoDeArquivo(
        processador=criar_processador(tipo),
        session_factory=SessionLocal,
        storage_raiz=settings.storage_path,
    )


# fila -> função que monta o handler
HANDLERS = {"lotes": criar_ingestao}
HANDLERS.update({tipo: criar_processamento(tipo) for tipo in PROCESSADORES})


def main() -> None:
    parser = argparse.ArgumentParser(description="Worker de processamento")
    parser.add_argument("--fila", required=True, choices=sorted(HANDLERS))
    args = parser.parse_args()
    configurar_logs(args.fila)

    handler = HANDLERS[args.fila]()
    Consumidor(args.fila, handler, settings.max_tentativas).iniciar()


if __name__ == "__main__":
    main()
