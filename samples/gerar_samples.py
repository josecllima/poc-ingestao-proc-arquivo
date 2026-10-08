"""Gera ZIPs de teste com dados fictícios (só biblioteca padrão do Python).

Uso, na raiz do projeto:
    python samples/gerar_samples.py

Cria samples/lote-1mb.zip com um arquivo de cerca de 1 MB de cada tipo,
cada um feito para cair numa regra de classificação do desafio.
"""
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


def csv_clientes() -> bytes:
    # colunas cliente_id e documento -> DOCUMENTO_CLIENTE
    linhas = ["cliente_id;documento;nome;cidade"]
    i, tamanho = 0, 0
    while tamanho < ALVO:
        i += 1
        linha = f"{i};{rnd.randint(10**10, 10**11 - 1)};{nome_ficticio()};Cidade {rnd.randint(1, 99)}"
        linhas.append(linha)
        tamanho += len(linha) + 1
    return ("\n".join(linhas) + "\n").encode("utf-8")


def xml_movimentos() -> bytes:
    # raiz <movimentos> -> DOCUMENTO_MOVIMENTO
    partes = ['<?xml version="1.0" encoding="UTF-8"?>', "<movimentos>"]
    i, tamanho = 0, 0
    while tamanho < ALVO:
        i += 1
        item = (f'  <movimento id="{i}"><conta>{rnd.randint(1000, 9999)}</conta>'
                f"<valor>{rnd.uniform(1, 5000):.2f}</valor><tipo>{rnd.choice(['C', 'D'])}</tipo></movimento>")
        partes.append(item)
        tamanho += len(item) + 1
    partes.append("</movimentos>")
    return "\n".join(partes).encode("utf-8")


def xml_clientes() -> bytes:
    # raiz <clientes> -> DOCUMENTO_CLIENTE
    partes = ['<?xml version="1.0" encoding="UTF-8"?>', "<clientes>"]
    i, tamanho = 0, 0
    while tamanho < ALVO:
        i += 1
        item = f'  <cliente id="{i}"><nome>{nome_ficticio()}</nome><documento>{rnd.randint(10**10, 10**11 - 1)}</documento></cliente>'
        partes.append(item)
        tamanho += len(item) + 1
    partes.append("</clientes>")
    return "\n".join(partes).encode("utf-8")


def txt_movimentos() -> bytes:
    # primeira linha começa com MOV| -> DOCUMENTO_MOVIMENTO
    linhas = ["MOV|LAYOUT01|ARQUIVO FICTICIO"]
    i, tamanho = 0, 0
    while tamanho < ALVO:
        i += 1
        linha = f"DET|{i:08d}|{rnd.randint(1000, 9999)}|{rnd.uniform(1, 5000):.2f}|{rnd.choice(['C', 'D'])}"
        linhas.append(linha)
        tamanho += len(linha) + 1
    linhas.append(f"TRL|{i:08d}")
    return ("\n".join(linhas) + "\n").encode("utf-8")


def json_produtos() -> bytes:
    # propriedade products -> DOCUMENTO_PRODUTO
    produtos, tamanho, i = [], 0, 0
    while tamanho < ALVO:
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


def main() -> None:
    arquivos = {
        "clientes.csv": csv_clientes(),
        "clientes.xml": xml_clientes(),
        "movimentos.xml": xml_movimentos(),
        "movimentos.txt": txt_movimentos(),
        "produtos.json": json_produtos(),
        "imagens/foto.png": png(),
    }
    destino = PASTA / "lote-1mb.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, conteudo in arquivos.items():
            z.writestr(nome, conteudo)
            print(f"  {nome:<20} {len(conteudo) / 1024:>8.0f} KB")
    print(f"Gerado {destino} ({destino.stat().st_size / 1024:.0f} KB compactado)")


if __name__ == "__main__":
    main()
