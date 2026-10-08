"""Status possíveis de um lote e de um arquivo.

StrEnum faz cada valor se comportar como string: grava direto no banco
("RECEBIDO") e continua com a segurança de um enum no código.
"""
from enum import StrEnum


class StatusLote(StrEnum):
    RECEBIDO = "RECEBIDO"
    EXTRAINDO = "EXTRAINDO"
    CLASSIFICANDO = "CLASSIFICANDO"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    CONCLUIDO_COM_ERROS = "CONCLUIDO_COM_ERROS"
    ERRO = "ERRO"


class StatusArquivo(StrEnum):
    IDENTIFICADO = "IDENTIFICADO"
    PENDENTE = "PENDENTE"
    PUBLICADO = "PUBLICADO"
    PROCESSANDO = "PROCESSANDO"
    PROCESSADO = "PROCESSADO"
    ARMAZENADO = "ARMAZENADO"
    ERRO = "ERRO"
    IGNORADO = "IGNORADO"
