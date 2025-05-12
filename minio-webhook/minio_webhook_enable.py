from minio import Minio
from minio.notificationconfig import NotificationConfig, QueueConfig
import logging
import os
import sys
import urllib3

minio_username = os.getenv('MINIO_USERNAME')
minio_password = os.getenv('MINIO_PASSWORD')
minio_endpoint = os.getenv('MINIO_ENDPOINT')
minio_bucket_name = os.getenv('MINIO_BUCKET_NAME')
minio_notification_config = NotificationConfig(
    queue_config_list=[
        QueueConfig(
            f"arn:minio:sqs::{minio_bucket_name}:webhook",
            ["s3:ObjectCreated:*"],
        ),
    ],
)

print(f"Create MinIO client for {endpoint}")
try:
    client = Minio(
        minio_endpoint,
        access_key=minio_username,
        secret_key=minio_password,
        http_client=urllib3.poolmanager.PoolManager(
            ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
        ),
    )
except Exception as e:
    print(f"Failed to create MinIO client: {e}")

print(f"Bucket name: {minio_bucket_name}")
found = client.bucket_exists(minio_bucket_name)
if not found:
    print(f"Bucket {minio_bucket_name} does not exist. Creating it")
    try:
        client.make_bucket(minio_bucket_name)
    except Exception as e:
        print(f"Failed to create bucket {minio_bucket_name}: {e}")
        sys.exit(1)

print(f"Adding webhook to bucket {minio_bucket_name}")
try:
    client.set_bucket_notification(minio_bucket_name, minio_notification_config)
except Exception as e:
    print(f"Failed to add webhook to bucket {minio_bucket_name}: {e}")
    sys.exit(2)
