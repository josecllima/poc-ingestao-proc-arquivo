"""Loop de consumo genérico, usado por todos os workers.

Garantias:
  - prefetch_count=1: cada worker pega uma mensagem por vez
  - ack manual: a mensagem só sai da fila depois de processada
  - ErroPermanente: registra a falha e confirma (retry não adiantaria)
  - qualquer outro erro: republica em queue.<tipo>.retry com tentativa+1;
    depois de MAX_TENTATIVAS, registra a falha e manda para a DLQ
  - se o RabbitMQ cair, reconecta sozinho com espera crescente
"""
import json
import logging
import time

import pika
from pika.exceptions import AMQPConnectionError, ChannelClosedByBroker, ConnectionClosedByBroker

from app.domain.errors import ErroPermanente
from app.infrastructure.messaging import ChannelPublisher, connection_params
from app.infrastructure.topology import declarar_topologia, fila

log = logging.getLogger(__name__)


class Consumidor:
    def __init__(self, tipo: str, handler, max_tentativas: int):
        self.tipo = tipo
        self.fila = fila(tipo)
        self.handler = handler  # objeto com processar(mensagem, publisher) e falhou(mensagem, motivo)
        self.max_tentativas = max_tentativas

    def iniciar(self) -> None:
        espera = 1
        while True:
            try:
                conn = pika.BlockingConnection(connection_params(attempts=1))
                channel = conn.channel()
                declarar_topologia(channel)
                channel.confirm_delivery()
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(self.fila, self._ao_receber)
                log.info("Worker pronto, consumindo fila=%s", self.fila)
                espera = 1
                channel.start_consuming()
            except (AMQPConnectionError, ConnectionClosedByBroker, ChannelClosedByBroker) as exc:
                log.warning("Conexão com o RabbitMQ perdida (%s). Nova tentativa em %ss", type(exc).__name__, espera)
                time.sleep(espera)
                espera = min(espera * 2, 30)
            except KeyboardInterrupt:
                log.info("Worker encerrado")
                return

    def _ao_receber(self, channel, method, properties, body) -> None:
        try:
            mensagem = json.loads(body)
        except ValueError:
            log.error("Mensagem ilegível na fila=%s, enviada para a DLQ", self.fila)
            channel.basic_nack(method.delivery_tag, requeue=False)
            return

        tentativa = int(mensagem.get("tentativa", 1))
        contexto = f"fila={self.fila} loteId={mensagem.get('loteId')} arquivoId={mensagem.get('arquivoId')} tentativa={tentativa}"
        try:
            self.handler.processar(mensagem, ChannelPublisher(channel))
            channel.basic_ack(method.delivery_tag)
        except ErroPermanente as exc:
            log.warning("Erro permanente, sem retry %s motivo=%s", contexto, exc)
            self._registrar_falha(mensagem, str(exc))
            channel.basic_ack(method.delivery_tag)
        except Exception as exc:  # falha transitória (banco fora, timeout...)
            motivo = f"{type(exc).__name__}: {exc}"[:900]
            if tentativa < self.max_tentativas:
                log.warning("Falha transitória, agendando retry %s motivo=%s", contexto, motivo)
                mensagem["tentativa"] = tentativa + 1
                channel.basic_publish(
                    exchange="",  # exchange padrão: entrega direto na fila pelo nome
                    routing_key=f"{self.fila}.retry",
                    body=json.dumps(mensagem).encode(),
                    properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
                )
                channel.basic_ack(method.delivery_tag)
            else:
                log.error("Tentativas esgotadas, enviando para a DLQ %s motivo=%s", contexto, motivo)
                self._registrar_falha(mensagem, motivo)
                channel.basic_nack(method.delivery_tag, requeue=False)

    def _registrar_falha(self, mensagem: dict, motivo: str) -> None:
        try:
            self.handler.falhou(mensagem, motivo)
        except Exception:
            log.exception("Não foi possível registrar a falha no banco")
