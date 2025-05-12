from minio import Minio
import os
import sys
import urllib3

MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')

def disable_webhook():
    username = os.getenv('MINIO_USERNAME')
    password = os.getenv('MINIO_PASSWORD')
    endpoint = os.getenv('MINIO_ENDPOINT')

    client = Minio(
        endpoint,
        access_key=username,
        secret_key=password,
        http_client=urllib3.poolmanager.PoolManager(
            ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
        ),
    )
    client.delete_bucket_notification(MINIO_BUCKET_NAME)

if __name__ == '__main__':
    try:
        disable_webhook()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

