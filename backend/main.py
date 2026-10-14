import uuid
import json
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, SessionLocal, Job
from minio_client import setup_buckets, minio_client, UPLOADS_BUCKET
from rabbitmq_client import setup_rabbitmq, get_rabbitmq_connection, QUEUE_CONVERSAO
import pika

app = FastAPI(title="API de Ingestão de Vídeo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    setup_buckets()
    setup_rabbitmq()

@app.post("/api/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
    file: UploadFile = File(...),
    targetFormat: str = Form(...),
    notifyEmail: str = Form(...)
):
    job_id = str(uuid.uuid4())
    filename = file.filename
    ext = filename.split(".")[-1].lower() if "." in filename else ""

    # Validação do formato de entrada (Apenas vídeo)
    if ext not in ["mp4", "avi", "mov", "mkv", "webm"]:
        raise HTTPException(
            status_code=400, 
            detail="Formato inválido. Envie apenas arquivos de vídeo (MP4, AVI, MOV, MKV, WEBM)."
        )

    object_name = f"{job_id}.{ext}"

    # 1. Envia vídeo original para o SeaweedFS
    contents = await file.read()
    minio_client.put_object(
        UPLOADS_BUCKET,
        object_name,
        BytesIO(contents),
        length=len(contents),
        content_type=file.content_type
    )

    source_url = f"http://seaweedfs:8333/{UPLOADS_BUCKET}/{object_name}"

    # 2. Grava registro no Banco de Dados
    db = SessionLocal()
    new_job = Job(
        id=job_id,
        notify_email=notifyEmail,
        source_type="video",
        source_format=ext,
        target_format=targetFormat.lower(),
        status="PENDENTE",
        source_url=source_url,
        attempts=1
    )
    db.add(new_job)
    db.commit()
    db.close()

    # 3. Publica mensagem de conversão no RabbitMQ
    payload = {
        "jobId": job_id,
        "sourceUrl": source_url,
        "sourceFormat": ext,
        "targetFormat": targetFormat.lower(),
        "notifyEmail": notifyEmail
    }

    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_CONVERSAO,
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()

    return {"jobId": job_id, "status": "PENDENTE", "message": "Vídeo recebido. A conversão foi iniciada."}

@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    db.close()

    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")

    return {
        "jobId": job.id,
        "status": job.status,
        "resultUrl": job.result_url,
        "errorMessage": job.error_message,
        "updatedAt": job.updated_at
    }