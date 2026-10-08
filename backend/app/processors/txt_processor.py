"""Seção 5.4: conta linhas e identifica o padrão da primeira linha."""
from app.domain.errors import ErroPermanente
from app.domain.status import StatusArquivo
from app.processors.base import ler_texto


class TxtProcessor:
    status_sucesso = StatusArquivo.PROCESSADO

    def processar(self, caminho):
        texto = ler_texto(caminho)
        linhas = texto.splitlines()
        if not linhas:
            raise ErroPermanente("TXT vazio")

        primeira = linhas[0].strip()
        if "|" in primeira:
            padrao = f"registro delimitado por '|', prefixo {primeira.split('|')[0]}"
        elif ";" in primeira:
            padrao = "registro delimitado por ';'"
        else:
            padrao = "texto livre"

        return {"linhas": len(linhas), "primeiraLinha": primeira[:200], "padraoPrimeiraLinha": padrao}
