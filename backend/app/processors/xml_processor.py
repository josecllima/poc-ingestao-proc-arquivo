"""Seção 5.3: verifica se está bem-formado, elemento raiz e total de elementos.

Lê em streaming (iterparse) e libera cada elemento depois de contado,
então um XML grande não ocupa a memória inteira. O ElementTree não resolve
entidades externas; em produção, usaria a biblioteca defusedxml.
"""
import xml.etree.ElementTree as ET

from app.domain.errors import ErroPermanente
from app.domain.status import StatusArquivo


class XmlProcessor:
    status_sucesso = StatusArquivo.PROCESSADO

    def processar(self, caminho):
        raiz, total = None, 0
        try:
            for evento, elemento in ET.iterparse(caminho, events=("start", "end")):
                if evento == "start":
                    total += 1
                    if raiz is None:
                        raiz = elemento.tag
                else:
                    elemento.clear()
        except ET.ParseError as exc:
            raise ErroPermanente(f"XML malformado: {exc}") from exc

        if raiz is None:
            raise ErroPermanente("XML sem elemento raiz")
        return {"elementoRaiz": raiz.split("}")[-1], "quantidadeElementos": total}
