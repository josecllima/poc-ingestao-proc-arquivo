"""Fila -> processador (padrão Factory).

Para suportar um tipo novo: criar o processador, registrar aqui, mapear a
extensão em domain/tipos.py e acrescentar o worker no docker-compose.
"""
from app.processors.csv_processor import CsvProcessor
from app.processors.json_processor import JsonProcessor
from app.processors.storage_processor import StorageProcessor
from app.processors.txt_processor import TxtProcessor
from app.processors.xml_processor import XmlProcessor

PROCESSADORES = {
    "csv": CsvProcessor,
    "json": JsonProcessor,
    "xml": XmlProcessor,
    "txt": TxtProcessor,
    "storage": StorageProcessor,
}


def criar_processador(tipo: str):
    return PROCESSADORES[tipo]()
