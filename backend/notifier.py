import os
import json
import time
import smtplib
from email.mime.text import MIMEText
import pika

from rabbitmq_client import get_rabbitmq_connection, setup_rabbitmq, QUEUE_NOTIFICACAO

SMTP_HOST = os.getenv("SMTP_HOST", "mailpit")
SMTP_PORT = int(os.getenv("SMTP_PORT", 1025))

def send_email(to_email, job_id, result_url):
    subject = "Sua conversão de áudio foi concluída!"
    body = f"""Olá,

Seu vídeo foi convertido em áudio com sucesso! (Job ID: {job_id})

Acesse seu arquivo de áudio no link abaixo:
{result_url}

Obrigado por utilizar nosso conversor!
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "no-reply@midia-converter.com"
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)
    print(f"[✉] E-mail enviado para {to_email} referente ao job {job_id}")

def process_notification(ch, method, properties, body):
    data = json.loads(body)
    job_id = data["jobId"]
    notify_email = data["notifyEmail"]
    result_url = data["resultUrl"]

    try:
        send_email(notify_email, job_id, result_url)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[X] Erro ao enviar e-mail: {str(e)}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

def start_notifier():
    retries = 10
    conn = None
    while retries > 0:
        try:
            setup_rabbitmq()
            conn = get_rabbitmq_connection()
            print("[✓] Serviço de Notificação conectado ao RabbitMQ com sucesso!")
            break
        except Exception as e:
            print(f"[*] Aguardando RabbitMQ para o Serviço de Notificação... ({retries} tentativas restantes)")
            time.sleep(3)
            retries -= 1

    if not conn:
        raise RuntimeError("Não foi possível conectar ao RabbitMQ no Notifier.")

    channel = conn.channel()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NOTIFICACAO, on_message_callback=process_notification)
    print("[*] Serviço de Notificação ouvindo eventos...")
    channel.start_consuming()

if __name__ == "__main__":
    start_notifier()