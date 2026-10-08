"""Erros de negócio.

O domínio não conhece HTTP. Quem traduz cada erro para um código de
status (400, 413, 503) é a API, em main.py.
"""


class ErroDeValidacao(Exception):
    """Entrada recusada (ex.: arquivo que não é .zip, arquivo vazio)."""


class LimiteExcedido(Exception):
    """Arquivo maior que o limite configurado."""


class FilaIndisponivel(Exception):
    """Não foi possível publicar a mensagem no RabbitMQ."""


class ErroPermanente(Exception):
    """Falha que não adianta tentar de novo (ex.: ZIP corrompido).

    O worker registra o erro e confirma a mensagem, sem retry.
    """
