"""Mapeamento das tabelas do banco (ORM do SQLAlchemy).

Equivale às entidades do Entity Framework. As tabelas já são criadas
pelo db/init.sql; aqui só dizemos ao Python como elas são.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class LoteModel(Base):
    __tablename__ = "lote"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_zip: Mapped[str]
    hash_sha256: Mapped[str | None]
    status: Mapped[str]
    total_arquivos: Mapped[int | None]
    mensagem_erro: Mapped[str | None]
    recebido_em: Mapped[datetime] = mapped_column(default=agora_utc)
    concluido_em: Mapped[datetime | None]


class ArquivoModel(Base):
    __tablename__ = "arquivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    lote_id: Mapped[int]
    nome: Mapped[str]
    caminho_relativo: Mapped[str]
    caminho_storage: Mapped[str | None]
    extensao: Mapped[str | None]
    tamanho_bytes: Mapped[int | None]
    tipo_documental: Mapped[str | None]
    fila: Mapped[str | None]
    status: Mapped[str]
    tentativas: Mapped[int] = mapped_column(default=0)
    resultado: Mapped[str | None]
    erro: Mapped[str | None]
    criado_em: Mapped[datetime] = mapped_column(default=agora_utc)
    iniciado_em: Mapped[datetime | None]
    finalizado_em: Mapped[datetime | None]
