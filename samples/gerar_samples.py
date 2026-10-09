"""Gera os ZIPs de teste com dados fictícios (só biblioteca padrão do Python).

Uso, na raiz do projeto:
    python samples/gerar_samples.py

Gera em samples/ (o resultado esperado de cada um está no README.md da pasta):
    lote-valido.zip                         um arquivo válido de cada tipo
    lote-com-erros.zip                      inválidos, vazio, duplicado, caminho malicioso
    lote-com-arquivos-nao-processaveis.zip  PDF, imagens e extensões desconhecidas
    lote-corrompido.zip                     não é um ZIP de verdade (lote inteiro em ERRO)
    lote-1mb.zip                            ~1 MB por arquivo, para teste de volume
"""
import base64
import json
import random
import struct
import zlib
import zipfile
from pathlib import Path

ALVO = 1024 * 1024  # 1 MB por arquivo
PASTA = Path(__file__).parent
rnd = random.Random(42)  # semente fixa: o ZIP sai igual toda vez


def nome_ficticio() -> str:
    return rnd.choice(["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio"]) + " " + \
        rnd.choice(["Teste", "Exemplo", "Ficticio", "Modelo"])


def csv_clientes(tamanho_alvo: int = ALVO) -> bytes:
    # colunas cliente_id e documento -> DOCUMENTO_CLIENTE
    linhas = ["cliente_id;documento;nome;cidade"]
    i, tamanho = 0, 0
    while tamanho < tamanho_alvo:
        i += 1
        linha = f"{i};{rnd.randint(10**10, 10**11 - 1)};{nome_ficticio()};Cidade {rnd.randint(1, 99)}"
        linhas.append(linha)
        tamanho += len(linha) + 1
    return ("\n".join(linhas) + "\n").encode("utf-8")


def xml_movimentos(tamanho_alvo: int = ALVO) -> bytes:
    # raiz <movimentos> -> DOCUMENTO_MOVIMENTO
    partes = ['<?xml version="1.0" encoding="UTF-8"?>', "<movimentos>"]
    i, tamanho = 0, 0
    while tamanho < tamanho_alvo:
        i += 1
        item = (f'  <movimento id="{i}"><conta>{rnd.randint(1000, 9999)}</conta>'
                f"<valor>{rnd.uniform(1, 5000):.2f}</valor><tipo>{rnd.choice(['C', 'D'])}</tipo></movimento>")
        partes.append(item)
        tamanho += len(item) + 1
    partes.append("</movimentos>")
    return "\n".join(partes).encode("utf-8")


def xml_clientes(tamanho_alvo: int = ALVO) -> bytes:
    # raiz <clientes> -> DOCUMENTO_CLIENTE
    partes = ['<?xml version="1.0" encoding="UTF-8"?>', "<clientes>"]
    i, tamanho = 0, 0
    while tamanho < tamanho_alvo:
        i += 1
        item = f'  <cliente id="{i}"><nome>{nome_ficticio()}</nome><documento>{rnd.randint(10**10, 10**11 - 1)}</documento></cliente>'
        partes.append(item)
        tamanho += len(item) + 1
    partes.append("</clientes>")
    return "\n".join(partes).encode("utf-8")


def txt_movimentos(tamanho_alvo: int = ALVO) -> bytes:
    # primeira linha começa com MOV| -> DOCUMENTO_MOVIMENTO
    linhas = ["MOV|LAYOUT01|ARQUIVO FICTICIO"]
    i, tamanho = 0, 0
    while tamanho < tamanho_alvo:
        i += 1
        linha = f"DET|{i:08d}|{rnd.randint(1000, 9999)}|{rnd.uniform(1, 5000):.2f}|{rnd.choice(['C', 'D'])}"
        linhas.append(linha)
        tamanho += len(linha) + 1
    linhas.append(f"TRL|{i:08d}")
    return ("\n".join(linhas) + "\n").encode("utf-8")


def json_produtos(tamanho_alvo: int = ALVO) -> bytes:
    # propriedade products -> DOCUMENTO_PRODUTO
    produtos, tamanho, i = [], 0, 0
    while tamanho < tamanho_alvo:
        i += 1
        p = {"id": i, "nome": f"Produto {i}", "preco": round(rnd.uniform(1, 999), 2), "estoque": rnd.randint(0, 500)}
        produtos.append(p)
        tamanho += len(json.dumps(p)) + 2
    return json.dumps({"products": produtos}, ensure_ascii=False, indent=1).encode("utf-8")


def png(largura: int = 600, altura: int = 580) -> bytes:
    # pixels aleatórios não comprimem: ~1 MB de PNG válido
    def bloco(tipo: bytes, dados: bytes) -> bytes:
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    linhas = b"".join(b"\x00" + rnd.randbytes(largura * 3) for _ in range(altura))
    return (b"\x89PNG\r\n\x1a\n"
            + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(linhas, 9))
            + bloco(b"IEND", b""))


# JPEG mínimo válido (16x16 azul), embutido para não depender de biblioteca de imagem
JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAA0JCgsKCA0LCgsODg0PEyAVExISEyccHhcgLikxMC4pLSwzOko+MzZGNywtQFdBRkxOUlNSMj5a"
    "YVpQYEpRUk//2wBDAQ4ODhMREyYVFSZPNS01T09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0//wAARCAAQ"
    "ABADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJx"
    "FDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWW"
    "l5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAEC"
    "AwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2"
    "Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU"
    "1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDBooor2jyj/9k="
)


def pdf(texto: str = "Comprovante ficticio - POC Certacon") -> bytes:
    """PDF de uma página, montado à mão (com a tabela xref correta)."""
    stream = f"BT /F1 14 Tf 72 720 Td ({texto}) Tj ET".encode("latin-1")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    saida = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objetos, start=1):
        offsets.append(len(saida))
        saida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(saida)
    saida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    saida += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    saida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(saida)


PEQUENO = 4 * 1024  # ~4 KB por arquivo nos lotes de demonstração

LOTES = {
    "lote-valido.zip": {
        "clientes.csv": lambda: csv_clientes(PEQUENO),
        "clientes.xml": lambda: xml_clientes(PEQUENO),
        "movimentos.xml": lambda: xml_movimentos(PEQUENO),
        "movimentos.txt": lambda: txt_movimentos(PEQUENO),
        "produtos.json": lambda: json_produtos(PEQUENO),
        "documentos/comprovante.pdf": pdf,
        "imagens/logo.png": lambda: png(32, 32),
    },
    "lote-com-erros.zip": {
        "clientes.csv": lambda: csv_clientes(PEQUENO),
        "csv-colunas-faltando.csv": lambda: b"cliente_id;documento;nome\n1;123;Ana Teste\n2;456\n",
        "json-quebrado.json": lambda: b'{"products": [{"id": 1, "nome": "Produto 1"',
        "xml-malformado.xml": lambda: b"<clientes><cliente><nome>Ana</cliente></clientes>",
        "pedidos.xml": lambda: b"<pedidos><pedido id='1'/></pedidos>",  # válido, tipo desconhecido
        "lista.json": lambda: b"[1, 2, 3]",  # válido, tipo desconhecido
        "vazio.txt": lambda: b"",
        "dados/relatorio.txt": lambda: b"Relatorio ficticio\nlinha 2\n",
        "DADOS/relatorio.txt": lambda: b"Nome duplicado (muda so a caixa)\n",
        "../fora-do-lote.txt": lambda: b"tentativa de path traversal",
    },
    "lote-com-arquivos-nao-processaveis.zip": {
        "documentos/contrato.pdf": lambda: pdf("Contrato ficticio"),
        "imagens/foto.jpg": lambda: JPEG,
        "imagens/grafico.png": lambda: png(64, 64),
        "planilha.xlsx": lambda: b"PK fake xlsx",
        "instalador.exe": lambda: b"MZ fake exe",
        "LEIAME": lambda: b"arquivo sem extensao",
    },
    "lote-1mb.zip": {
        "clientes.csv": csv_clientes,
        "clientes.xml": xml_clientes,
        "movimentos.xml": xml_movimentos,
        "movimentos.txt": txt_movimentos,
        "produtos.json": json_produtos,
        "imagens/foto.png": png,
    },
}


def main() -> None:
    for nome_zip, arquivos in LOTES.items():
        destino = PASTA / nome_zip
        with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
            for nome, gerar in arquivos.items():
                z.writestr(nome, gerar())
        print(f"{nome_zip:<42} {len(arquivos):>2} arquivos  {destino.stat().st_size / 1024:>7.0f} KB")

    (PASTA / "lote-corrompido.zip").write_bytes(b"isto nao e um arquivo zip\n" * 10)
    print(f"{'lote-corrompido.zip':<42}  -            1 KB")


if __name__ == "__main__":
    main()
