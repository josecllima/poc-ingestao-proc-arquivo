"""Extração segura do ZIP.

Protege contra os ataques e problemas comuns de arquivos compactados:
  - path traversal: nomes como "../../etc/passwd" ou "C:\\x" são recusados
  - ZIP bomb: limite de quantidade de arquivos e de tamanho descompactado,
    conferido nos bytes realmente escritos (o cabeçalho do ZIP pode mentir)
  - nomes duplicados: recebem sufixo _1, _2...
  - ZIP corrompido ou protegido por senha
"""
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from app.domain.errors import ErroPermanente

CHUNK = 1024 * 1024


@dataclass
class ArquivoExtraido:
    nome: str                  # nome do arquivo (ex.: foto.png)
    caminho_relativo: str      # caminho dentro do ZIP (ex.: imagens/foto.png)
    caminho: Path | None       # onde foi gravado; None se não foi extraído
    extensao: str
    tamanho: int
    erro: str | None = None    # motivo, quando o arquivo não pôde ser extraído


def _caminho_seguro(nome_no_zip: str) -> str | None:
    """Normaliza o caminho; None se ele tentar sair da pasta do lote."""
    partes = PurePosixPath(nome_no_zip.replace("\\", "/")).parts
    if not partes or partes[0] == "/" or ":" in partes[0] or ".." in partes:
        return None
    return "/".join(partes)


def _sem_duplicata(caminho: str, usados: set[str]) -> str:
    if caminho.lower() not in usados:
        usados.add(caminho.lower())
        return caminho
    p = PurePosixPath(caminho)
    n = 1
    while True:
        candidato = str(p.with_name(f"{p.stem}_{n}{p.suffix}"))
        if candidato.lower() not in usados:
            usados.add(candidato.lower())
            return candidato
        n += 1


class ExtratorZip:
    def __init__(self, max_arquivos: int, max_bytes_descompactados: int):
        self.max_arquivos = max_arquivos
        self.max_bytes = max_bytes_descompactados

    def extrair(self, zip_path: Path, destino: Path) -> list[ArquivoExtraido]:
        try:
            with zipfile.ZipFile(zip_path) as z:
                entradas = [e for e in z.infolist()
                            if not e.is_dir() and not e.filename.startswith("__MACOSX/")]

                if len(entradas) > self.max_arquivos:
                    raise ErroPermanente(f"O ZIP tem {len(entradas)} arquivos; o limite é {self.max_arquivos}")
                if sum(e.file_size for e in entradas) > self.max_bytes:
                    raise ErroPermanente("O conteúdo descompactado excede o limite permitido")

                destino.mkdir(parents=True, exist_ok=True)
                usados: set[str] = set()
                total = 0
                resultado = []
                for entrada in entradas:
                    item, escritos = self._extrair_entrada(z, entrada, destino, usados, self.max_bytes - total)
                    total += escritos
                    resultado.append(item)
                return resultado
        except zipfile.BadZipFile as exc:
            raise ErroPermanente("Arquivo ZIP corrompido ou inválido") from exc

    def _extrair_entrada(self, z, entrada, destino, usados, bytes_restantes):
        nome_original = entrada.filename
        nome = PurePosixPath(nome_original.replace("\\", "/")).name
        extensao = PurePosixPath(nome).suffix.lower().lstrip(".")

        relativo = _caminho_seguro(nome_original)
        if relativo is None:
            return ArquivoExtraido(nome, nome_original, None, extensao, entrada.file_size,
                                   "Caminho inseguro dentro do ZIP"), 0
        if entrada.flag_bits & 0x1:
            return ArquivoExtraido(nome, relativo, None, extensao, entrada.file_size,
                                   "Arquivo protegido por senha"), 0

        relativo = _sem_duplicata(relativo, usados)
        alvo = destino / relativo
        alvo.parent.mkdir(parents=True, exist_ok=True)

        escritos = 0
        try:
            with z.open(entrada) as origem, alvo.open("wb") as saida:
                while chunk := origem.read(CHUNK):
                    escritos += len(chunk)
                    if escritos > bytes_restantes:
                        raise ErroPermanente("O conteúdo descompactado excede o limite permitido")
                    saida.write(chunk)
        except (zipfile.BadZipFile, OSError, EOFError) as exc:
            alvo.unlink(missing_ok=True)
            return ArquivoExtraido(nome, relativo, None, extensao, entrada.file_size,
                                   f"Falha ao extrair: {type(exc).__name__}"), 0

        return ArquivoExtraido(PurePosixPath(relativo).name, relativo, alvo, extensao, escritos), escritos

    @staticmethod
    def limpar(destino: Path) -> None:
        shutil.rmtree(destino, ignore_errors=True)
