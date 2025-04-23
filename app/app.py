from flask import Flask, request
import json
import kfp
import os
import requests

app = Flask(__name__)

MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')
KFP_ENDPOINT = 'https://ds-pipeline-dspa.at-test.svc.cluster.local:8443'
KFP_PIPELINE_NAME = os.getenv('KFP_PIPELINE_NAME')

@app.route('/healthz', methods=['GET'])
def health():
    return {"status": "success"}, 200

@app.route('/minio-webhook', methods=['POST'])
def handle_minio_event():
    event_data = request.get_json()
    app.logger.warning("Received MinIO event:", json.dumps(event_data, indent=2))

    for record in event_data.get('Records', []):
        object_key = record['s3']['object']['key']
        app.logger.info(f"New object in bucket {MINIO_BUCKET_NAME}: {object_key}")
        trigger_pipeline(object_key)

    return {"status": "success"}, 200

def trigger_pipeline(bucket, object_key):
    params = {
        "bucket": MINIO_BUCKET_NAME,
        "object": object_key,
    }

    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as file:
        k8s_namespace = file.read().replace('\n', '')

    with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as file:
        k8s_token = file.read().replace('\n', '')

    client = kfp.client.Client(
        host=os.getenv('KUBERNETES_SERVICE_HOST'),
        namespace=k8s_namespace,
        existing_token=k8s_token,
        ssl_ca_cert='/var/run/secrets/kubernetes.io/serviceaccount/ca.crt',
    )

    try:
        pipeline_id = client.get_pipeline_id(KFP_PIPELINE_NAME)
        try:
            pipeline_run = client.run_pipeline(pipeline_id=pipeline_id, params=params)
            app.logger.info(f"Triggered pipeline run '{pipeline_run.name}'")
        except Exception as e:
            app.logger.error(f"Error triggering pipeline: {e}")
    except Exception as e:
        app.logger.error(f"Cannot find pipeline '{KFP_PIPELINE_NAME}'")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
