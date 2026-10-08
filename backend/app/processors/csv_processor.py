"""Seção 5.1 do desafio: delimitador, linhas, colunas e nomes das colunas.

Regra de validade (documentada no README): o arquivo precisa ter cabeçalho
e todas as linhas precisam ter a mesma quantidade de colunas que ele.
"""
import csv
import io

from app.domain.errors import ErroPermanente
from app.domain.status import StatusArquivo
from app.processors.base import ler_texto

DELIMITADORES = ";,|\t"


class CsvProcessor:
    status_sucesso = StatusArquivo.PROCESSADO

    def processar(self, caminho):
        texto = ler_texto(caminho)
        if not texto.strip():
            raise ErroPermanente("CSV vazio")

        amostra = texto[:65536]
        try:
            delimitador = csv.Sniffer().sniff(amostra, delimiters=DELIMITADORES).delimiter
        except csv.Error:
            # uma coluna só, ou formato que o Sniffer não reconhece
            primeira = amostra.splitlines()[0]
            delimitador = next((d for d in DELIMITADORES if d in primeira), ",")

        leitor = csv.reader(io.StringIO(texto), delimiter=delimitador)
        try:
            cabecalho = next(leitor)
        except (StopIteration, csv.Error) as exc:
            raise ErroPermanente(f"CSV ilegível: {exc}") from exc
        cabecalho = [c.strip() for c in cabecalho]
        if not any(cabecalho):
            raise ErroPermanente("CSV sem cabeçalho")

        linhas = 0
        try:
            for numero, linha in enumerate(leitor, start=2):
                if not linha or not any(campo.strip() for campo in linha):
                    continue  # linha em branco não conta
                if len(linha) != len(cabecalho):
                    raise ErroPermanente(
                        f"Linha {numero} tem {len(linha)} colunas; o cabeçalho tem {len(cabecalho)}")
                linhas += 1
        except csv.Error as exc:
            raise ErroPermanente(f"CSV malformado: {exc}") from exc

        return {
            "delimitador": "\\t" if delimitador == "\t" else delimitador,
            "linhas": linhas,
            "colunas": len(cabecalho),
            "nomesColunas": cabecalho,
        }
