import pika

from app.config import settings


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