"""Registro dos classificadores.

Para criar uma regra nova: escrever a classe em regras.py e acrescentá-la
em CLASSIFICADORES. O fluxo de ingestão não muda.
"""
from pathlib import Path

from app.classifiers.base import Classificador
from app.classifiers.regras import CsvPorColunas, JsonPorPropriedade, TxtPorPrefixo, XmlPorElementoRaiz
from app.domain import tipos

CLASSIFICADORES: list[Classificador] = [
    XmlPorElementoRaiz(),
    JsonPorPropriedade(),
    CsvPorColunas(),
    TxtPorPrefixo(),
]


class RegistroDeClassificadores:
    def __init__(self, classificadores: list[Classificador] | None = None):
        self.classificadores = classificadores if classificadores is not None else CLASSIFICADORES

    def classificar(self, extensao: str, caminho: Path) -> str:
        for classificador in self.classificadores:
            if tipo := classificador.classificar(extensao, caminho):
                return tipo
        return tipos.TIPO_DESCONHECIDO
