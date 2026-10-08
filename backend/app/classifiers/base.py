"""Contrato dos classificadores (equivale a uma interface do C#)."""
from pathlib import Path
from typing import Protocol


class Classificador(Protocol):
    def classificar(self, extensao: str, caminho: Path) -> str | None:
        """Retorna o tipo documental, ou None se esta regra não se aplica."""
        ...
