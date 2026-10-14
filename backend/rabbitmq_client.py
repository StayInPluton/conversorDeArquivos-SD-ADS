import os
import pika

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")

QUEUE_CONVERSAO = "conversao_queue"
QUEUE_DLQ = "conversao_dlq"
QUEUE_NOTIFICACAO = "notificacao_queue"

def get_rabbitmq_connection():
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    return pika.BlockingConnection(parameters)

def setup_rabbitmq():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # DLQ Setup
    channel.queue_declare(queue=QUEUE_DLQ, durable=True)

    # Fila de Conversão com suporte a DLQ
    channel.queue_declare(
        queue=QUEUE_CONVERSAO,
        durable=True,
        arguments={
            'x-dead-letter-exchange': '',
            'x-dead-letter-routing-key': QUEUE_DLQ
        }
    )

    # Fila de Notificação
    channel.queue_declare(queue=QUEUE_NOTIFICACAO, durable=True)

    connection.close()