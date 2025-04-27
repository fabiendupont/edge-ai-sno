from minio import Minio
import os
import sys

MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')

def enable_webhook():
    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as file:
        k8s_namespace = file.read().replace('\n', '')

    username = os.getenv('MINIO_ROOT_USER')
    password = os.getenv('MINIO_ROOT_PASSWORD')
    host = f"{os.getenv('MINIO_SERVICE_NAME')}.{k8s_namespace}.svc"
    port = os.getenv('MINIO_SERVICE_SERVICE_PORT_API')

    client = Minio(
        f"{host}:{port}",
        access_key=username,
        secret_key=password,
    )
    client.delete_bucket_notification(MINIO_BUCKET_NAME)

if __name__ == '__main__':
    try:
        enable_webhook()
    except S3Error as e:
        print(f"Error: {e}")
        sys.exit(1)

