"""Conexão e publicação no RabbitMQ."""
import json
import logging

import pika

from app.config import settings
from app.infrastructure.topology import EXCHANGE, declarar_topologia

log = logging.getLogger(__name__)


def connection_params(attempts: int = 5) -> pika.ConnectionParameters:
    return pika.ConnectionParameters(
        host=settings.rabbit_host,
        port=settings.rabbit_port,
        credentials=pika.PlainCredentials(settings.rabbit_user, settings.rabbit_password),
        heartbeat=60,
        blocked_connection_timeout=30,
        connection_attempts=attempts,
        retry_delay=3,
    )


def ping() -> None:
    conn = pika.BlockingConnection(connection_params(attempts=1))
    conn.close()


def preparar_topologia() -> None:
    """Cria exchanges e filas. Chamado quando a API (e depois os workers) sobem."""
    conn = pika.BlockingConnection(connection_params(attempts=10))
    try:
        declarar_topologia(conn.channel())
        log.info("Topologia do RabbitMQ declarada")
    finally:
        conn.close()


class RabbitPublisher:
    """Publica com confirmação do broker e mensagem persistente.

    Abre uma conexão por publicação porque a BlockingConnection do pika não
    é segura entre threads. Suficiente para a POC; em produção, um pool.
    """

    def publicar(self, routing_key: str, mensagem: dict) -> None:
        conn = pika.BlockingConnection(connection_params(attempts=3))
        try:
            channel = conn.channel()
            channel.confirm_delivery()  # basic_publish lança erro se o broker não confirmar
            channel.basic_publish(
                exchange=EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(mensagem).encode(),
                properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
                mandatory=True,  # lança erro se nenhuma fila receber a mensagem
            )
        finally:
            conn.close()


class ChannelPublisher:
    """Publica reaproveitando o canal do worker (sem abrir conexão nova).

    O canal precisa estar em modo de confirmação (confirm_delivery).
    """

    def __init__(self, channel):
        self.channel = channel

    def publicar(self, routing_key: str, mensagem: dict) -> None:
        self.channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(mensagem).encode(),
            properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
            mandatory=True,
        )
