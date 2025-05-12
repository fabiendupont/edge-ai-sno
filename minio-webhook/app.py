from flask import Flask, request, jsonify
from minio import Minio
import json
import logging
import os
import requests
import urllib3

app = Flask(__name__)


@app.route('/healthz', methods=['GET'])
def health():
    return {"status": "success"}, 200

@app.route('/minio-webhook', methods=['POST'])
def handle_minio_event():
    event_data = request.get_json()
    app.logger.info(f"Received MinIO event: {json.dumps(event_data)}")

    minio_endpoint = os.getenv('MINIO_ENDPOINT')
    minio_username = os.getenv('MINIO_USERNAME')
    minio_password = os.getenv('MINIO_PASSWORD')
    minio_bucket_name = os.getenv('MINIO_BUCKET_NAME')

    client = Minio(
        minio_endpoint,
        access_key=minio_username,
        secret_key=minio_password,
        http_client=urllib3.poolmanager.PoolManager(
            ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
        ),
    )

    app.logger.info("Iterating over all records")
    try:
        for record in event_data.get('Records', []):
            minio_object = client.get_object(
                minio_bucket_name,
                record['s3']['object']['key'],
            )
            app.logger.info(f"New object in bucket {minio_bucket_name}:\n{minio_object.data}")
    except Exception as e:
        app.logger.error(f"Failure to get object: {record['s3']['object']['key']}: {e}")
        return {"status": "failure"}, 500
    return {"status": "success"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

