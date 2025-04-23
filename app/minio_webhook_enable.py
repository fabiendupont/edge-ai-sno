from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig
import os
import sys
import urllib3

NOTIFICATION_CONFIG = NotificationConfig(
    queue_config_list=[
        QueueConfig(
            "arn:minio:sqs::kfp:webhook",
            ["s3:ObjectCreated:*"],
        ),
    ],
)

def enable_webhook():
    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as file:
        k8s_namespace = file.read().replace('\n', '')

    username = os.getenv('MINIO_ROOT_USER')
    password = os.getenv('MINIO_ROOT_PASSWORD')
    host = f"{os.getenv('MINIO_SERVICE_NAME')}.{k8s_namespace}.svc"
    port = os.getenv('MINIO_SERVICE_PORT_API')
    bucket_name = os.getenv('MINIO_BUCKET_NAME')

    client = Minio(
        f"{host}:{port}",
        access_key=username,
        secret_key=password,
        http_client=urllib3.poolmanager.PoolManager(
            ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
        ),
    )

    print(f"Bucket name: {bucket_name}")
    found = client.bucket_exists(bucket_name)
    if not found:
        print(f"Bucket {bucket_name} does not exist. Creating it")
        try:
            client.make_bucket(bucket_name)
        except Exception as e:
            print(f"Failed to create bucket {bucket_name}: {e}")
            sys.exit(1)
    print(f"Adding webhook to bucket {bucket_name}")
    try:
        client.set_bucket_notification(bucket_name, NOTIFICATION_CONFIG)
    except Exception as e:
        print(f"Failed to add webhook to bucket {bucket_name}: {e}")
        sys.exit(2)

if __name__ == '__main__':
        enable_webhook()
