"""Filas e exchanges do RabbitMQ.

Cada tipo tem três filas:
  queue.<tipo>        principal, onde o worker consome
  queue.<tipo>.retry  espera RETRY_TTL_MS e devolve a mensagem para a principal
  queue.<tipo>.dlq    destino final de mensagens que falharam demais

Declarar é idempotente: rodar de novo não apaga nem duplica nada.
"""
EXCHANGE = "ingestao"
DLX = "ingestao.dlx"
TIPOS = ("lotes", "csv", "json", "xml", "txt", "storage")
RETRY_TTL_MS = 5000


def fila(tipo: str) -> str:
    return f"queue.{tipo}"


def declarar_topologia(channel) -> None:
    channel.exchange_declare(EXCHANGE, exchange_type="direct", durable=True)
    channel.exchange_declare(DLX, exchange_type="direct", durable=True)

    for tipo in TIPOS:
        principal = fila(tipo)
        channel.queue_declare(principal, durable=True, arguments={
            "x-dead-letter-exchange": DLX,
            "x-dead-letter-routing-key": tipo,
        })
        channel.queue_bind(principal, EXCHANGE, routing_key=tipo)

        channel.queue_declare(f"{principal}.retry", durable=True, arguments={
            "x-message-ttl": RETRY_TTL_MS,
            "x-dead-letter-exchange": EXCHANGE,
            "x-dead-letter-routing-key": tipo,
        })

        channel.queue_declare(f"{principal}.dlq", durable=True)
        channel.queue_bind(f"{principal}.dlq", DLX, routing_key=tipo)
