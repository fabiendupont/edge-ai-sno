from minio import Minio
import os
import sys
import urllib3

minio_username = os.getenv('MINIO_USERNAME')
minio_password = os.getenv('MINIO_PASSWORD')
minio_endpoint = os.getenv('MINIO_ENDPOINT')
minio_bucket_name = os.getenv('MINIO_BUCKET_NAME')

client = Minio(
    minio_endpoint,
    access_key=minio_username,
    secret_key=minio_password,
    http_client=urllib3.poolmanager.PoolManager(
        ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
    ),
)
client.delete_bucket_notification(minio_bucket_name)
