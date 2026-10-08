"""Seção 5.2: valida, identifica objeto ou lista e conta o primeiro nível."""
import json

from app.domain.errors import ErroPermanente
from app.domain.status import StatusArquivo
from app.processors.base import ler_texto


class JsonProcessor:
    status_sucesso = StatusArquivo.PROCESSADO

    def processar(self, caminho):
        try:
            conteudo = json.loads(ler_texto(caminho))
        except ValueError as exc:
            raise ErroPermanente(f"JSON inválido: {exc}") from exc

        if isinstance(conteudo, dict):
            return {"estrutura": "objeto", "elementosPrimeiroNivel": len(conteudo),
                    "chaves": list(conteudo)[:50]}
        if isinstance(conteudo, list):
            return {"estrutura": "lista", "elementosPrimeiroNivel": len(conteudo)}
        return {"estrutura": type(conteudo).__name__, "elementosPrimeiroNivel": 1}
