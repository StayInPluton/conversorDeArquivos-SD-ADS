import os
import json
import time
import subprocess
import pika

from database import SessionLocal, Job
from minio_client import minio_client, UPLOADS_BUCKET, CONVERTED_BUCKET
from rabbitmq_client import get_rabbitmq_connection, setup_rabbitmq, QUEUE_CONVERSAO, QUEUE_NOTIFICACAO

PUBLIC_MINIO_URL = os.getenv("PUBLIC_MINIO_URL", "http://localhost:9000")

def process_conversion(ch, method, properties, body):
    data = json.loads(body)
    job_id = data["jobId"]
    source_format = data["sourceFormat"]
    target_format = data["targetFormat"]
    notify_email = data["notifyEmail"]

    print(f"[*] Extraindo áudio do Vídeo (Job {job_id}): {source_format} -> {target_format}")

    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()

    if job:
        job.status = "PROCESSANDO"
        db.commit()

    source_filename = f"{job_id}.{source_format}"
    converted_filename = f"{job_id}.{target_format}"
    local_source = f"/tmp/{source_filename}"
    local_converted = f"/tmp/{converted_filename}"

    try:
        # 1. Download do vídeo original do SeaweedFS
        minio_client.fget_object(UPLOADS_BUCKET, source_filename, local_source)

        # 2. Conversão de Vídeo para Áudio via FFmpeg
        cmd = ["ffmpeg", "-y", "-i", local_source, "-vn", local_converted]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 3. Upload do arquivo de áudio resultante
        minio_client.fput_object(CONVERTED_BUCKET, converted_filename, local_converted)

        # 4. Gerar link público
        public_url = f"{PUBLIC_MINIO_URL}/{CONVERTED_BUCKET}/{converted_filename}"

        # 5. Remover arquivo de vídeo original do bucket de uploads
        minio_client.remove_object(UPLOADS_BUCKET, source_filename)

        # 6. Atualizar status no banco
        if job:
            job.status = "CONCLUÍDO"
            job.result_url = public_url
            db.commit()

        # 7. Publicar evento para o serviço de notificação
        event_payload = {
            "jobId": job_id,
            "resultUrl": public_url,
            "notifyEmail": notify_email
        }
        ch.basic_publish(
            exchange='',
            routing_key=QUEUE_NOTIFICACAO,
            body=json.dumps(event_payload),
            properties=pika.BasicProperties(delivery_mode=2)
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[✓] Vídeo convertido em Áudio com sucesso! Job: {job_id}")

    except Exception as e:
        print(f"[X] Erro no processamento do Job {job_id}: {str(e)}")
        if job:
            job.status = "ERRO"
            job.error_message = str(e)
            db.commit()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    finally:
        db.close()
        for f in [local_source, local_converted]:
            if os.path.exists(f):
                os.remove(f)

def start_worker():
    retries = 10
    conn = None
    while retries > 0:
        try:
            setup_rabbitmq()
            conn = get_rabbitmq_connection()
            print("[✓] Worker conectado ao RabbitMQ com sucesso!")
            break
        except Exception as e:
            print(f"[*] Aguardando RabbitMQ inicializar e criar filas... ({retries} tentativas restantes)")
            time.sleep(3)
            retries -= 1

    if not conn:
        raise RuntimeError("Não foi possível conectar ao RabbitMQ no Worker.")

    channel = conn.channel()
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_CONVERSAO, on_message_callback=process_conversion)
    print("[*] Worker de Mídia pronto para converter vídeos em áudio...")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()