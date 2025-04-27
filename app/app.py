from flask import Flask, request, jsonify
import kfp
import logging
import os
import requests

app = Flask(__name__)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')
KFP_PIPELINE_ENDPOINT = os.getenv('KFP_PIPELINE_ENDPOINT')
KFP_PIPELINE_NAME = os.getenv('KFP_PIPELINE_NAME')

@app.route('/healthz', methods=['GET'])
def health():
    return {"status": "success"}, 200

@app.route('/minio-webhook', methods=['POST'])
def handle_minio_event():
    event_data = request.get_json()
    app.logger.info(f"Received MinIO event: {jsonify(event_data)}")

    for record in event_data.get('Records', []):
        object_key = record['s3']['object']['key']
        app.logger.info(f"New object in bucket {MINIO_BUCKET_NAME}: {object_key}")
        try:
            _trigger_pipeline(object_key)
        except:
            return {"status": "failure"}, 500
    return {"status": "success"}, 200

def _trigger_pipeline(object_key):
    params = {
        "bucket": MINIO_BUCKET_NAME,
        "object": object_key,
    }
    app.logger.info(f"Trigger pipeline start - {object_key}")

    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as file:
        k8s_namespace = file.read().replace('\n', '')
    app.logger.info(f"Namespace: {k8s_namespace}")

    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as file:
        k8s_token = file.read().replace('\n', '')

    client = kfp.client.Client(
        host=KFP_PIPELINE_ENDPOINT,
        namespace=k8s_namespace,
        existing_token=k8s_token,
        ssl_ca_cert='/var/run/secrets/kubernetes.io/serviceaccount/ca.crt',
    )

    try:
        pipeline_id = client.get_pipeline_id(KFP_PIPELINE_NAME)
        app.logger.info(f"Pipeline id: {pipeline_id}")
        try:
            pipeline_run = client.run_pipeline(pipeline_id=pipeline_id, params=params)
            app.logger.info(f"Triggered pipeline run '{pipeline_run.name}'")
        except Exception as e:
            app.logger.error(f"Error triggering pipeline: {e}")
    except Exception as e:
        app.logger.error(f"Cannot find pipeline '{KFP_PIPELINE_NAME}': {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
