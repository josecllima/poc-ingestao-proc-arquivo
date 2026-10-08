"""Uma classe por regra de classificação (padrão Strategy).

Cada regra olha o CONTEÚDO do arquivo, não o nome. Uma regra que não
reconhece o arquivo, ou não consegue lê-lo, devolve None e deixa a
próxima tentar. Validar o arquivo de verdade é trabalho do worker do tipo.
"""
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from app.domain import tipos


def _primeira_linha(caminho: Path) -> str:
    with caminho.open("r", encoding="utf-8-sig", errors="replace") as f:
        return f.readline().strip()


class XmlPorElementoRaiz:
    MAPA = {"clientes": tipos.DOCUMENTO_CLIENTE, "movimentos": tipos.DOCUMENTO_MOVIMENTO}

    def classificar(self, extensao, caminho):
        if extensao != "xml":
            return None
        try:
            # iterparse para no primeiro elemento: não carrega o arquivo inteiro
            for _evento, elemento in ET.iterparse(caminho, events=("start",)):
                return self.MAPA.get(elemento.tag.lower())
        except ET.ParseError:
            return None
        return None


class JsonPorPropriedade:
    MAPA = {"products": tipos.DOCUMENTO_PRODUTO}

    def classificar(self, extensao, caminho):
        if extensao != "json":
            return None
        try:
            with caminho.open("r", encoding="utf-8-sig") as f:
                conteudo = json.load(f)
        except (ValueError, UnicodeDecodeError):
            return None
        if isinstance(conteudo, dict):
            for chave, tipo in self.MAPA.items():
                if chave in conteudo:
                    return tipo
        return None


class CsvPorColunas:
    REGRAS = [({"cliente_id", "documento"}, tipos.DOCUMENTO_CLIENTE)]

    def classificar(self, extensao, caminho):
        if extensao != "csv":
            return None
        cabecalho = _primeira_linha(caminho)
        try:
            delimitador = csv.Sniffer().sniff(cabecalho, delimiters=";,|\t").delimiter
        except csv.Error:
            delimitador = ","
        colunas = {c.strip().lower() for c in cabecalho.split(delimitador)}
        for obrigatorias, tipo in self.REGRAS:
            if obrigatorias <= colunas:
                return tipo
        return None


class TxtPorPrefixo:
    REGRAS = [("MOV|", tipos.DOCUMENTO_MOVIMENTO)]

    def classificar(self, extensao, caminho):
        if extensao != "txt":
            return None
        linha = _primeira_linha(caminho)
        for prefixo, tipo in self.REGRAS:
            if linha.startswith(prefixo):
                return tipo
        return None
