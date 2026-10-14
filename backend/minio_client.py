import os
import time
from minio import Minio

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "seaweedfs:8333")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "any_key")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "any_secret")

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

UPLOADS_BUCKET = "uploads"
CONVERTED_BUCKET = "converted"

def setup_buckets():
    """Tenta conectar ao SeaweedFS S3 com retentativas ate o servico estar pronto."""
    retries = 10
    while retries > 0:
        try:
            for bucket in [UPLOADS_BUCKET, CONVERTED_BUCKET]:
                if not minio_client.bucket_exists(bucket):
                    minio_client.make_bucket(bucket)
            print("[✓] Buckets do SeaweedFS criados/verificados com sucesso!")
            return
        except Exception as e:
            print(f"[*] Aguardando SeaweedFS S3 inicializar na porta 8333... ({retries} tentativas restantes)")
            time.sleep(3)
            retries -= 1

    raise RuntimeError("Nao foi possivel conectar ao SeaweedFS S3 apos multiplas tentativas.")