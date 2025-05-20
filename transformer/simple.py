# Copyright 2021 The KServe Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import base64
import io
import json
import os
import urllib.parse
import sys
from datetime import datetime
from typing import Dict, Union

import numpy as np

from kserve import (
    Model,
    ModelServer,
    model_server,
    InferInput,
    InferRequest,
    InferResponse,
    logging,
)
from kserve.model import PredictorProtocol, PredictorConfig

from minio import Minio
import urllib3

def get_minio_client():
    minio_endpoint = os.getenv('MINIO_ENDPOINT')
    minio_username = os.getenv('MINIO_USERNAME')
    minio_password = os.getenv('MINIO_PASSWORD')
    minio_use_https = os.getenv('MINIO_USE_HTTPS', '0')

    print(f"Creating MinIO client for {minio_endpoint}")
    if minio_use_https == '1':
        client = Minio(
            minio_endpoint,
            access_key=minio_username,
            secret_key=minio_password,
            http_client=urllib3.poolmanager.PoolManager(
                ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
            ),
        )
    else:
        client = Minio(
            minio_endpoint,
            access_key=minio_username,
            secret_key=minio_password,
            secure=False
        )

    return client

class SimpleTransformer(Model):
    def __init__(
        self,
        name: str,
        predictor_host: str,
        predictor_protocol: str,
        predictor_use_ssl: bool,
        minio_client,
    ):
        super().__init__(
            name,
            PredictorConfig(predictor_host, predictor_protocol, predictor_use_ssl),
            return_response_headers=True,
        )
        self.minio_client = minio_client
        self.ready = True

    def preprocess(
        self, payload: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Union[Dict, InferRequest]:
        minio_bucket_name = os.getenv('MINIO_INPUT_BUCKET_NAME')

        if isinstance(payload, InferRequest):
            input_tensors = payload.inputs[0].data
        else:
            headers["request-type"] = "v1"
            # Input follows the Tensorflow V1 HTTP API for binary values
            # https://www.tensorflow.org/tfx/serving/api_rest#encoding_binary_values
            batch_size = len(payload["Records"])
            input_data = None
            filename = None
            for indx, record in enumerate(payload["Records"]):
                filename = urllib.parse.unquote(record["s3"]["object"]["key"])
                minio_object = self.minio_client.get_object(minio_bucket_name, filename)
                sample = np.load(io.BytesIO(minio_object.read()), allow_pickle=True)
                if input_data is None:
                    input_data = np.empty((batch_size,)+sample.shape, dtype=sample.dtype)
                input_data[indx] = (sample / np.average(sample)).astype(np.float32)

        infer_inputs = [
            InferInput(
                name="input_4",
                datatype="FP32",
                shape=input_data.shape,
                data=input_data.tolist(),
            )
        ]
        infer_request = InferRequest(
            request_id=filename,
            model_name=self.name,
            infer_inputs=infer_inputs,
        )

        return infer_request

    def postprocess(
        self,
        infer_response: Union[Dict, InferResponse],
        headers: Dict[str, str] = None,
        response_headers: Dict[str, str] = None,
    ) -> Union[Dict, InferResponse]:
        minio_bucket_name = os.getenv('MINIO_OUTPUT_BUCKET_NAME')

        predictions = io.BytesIO(json.dumps(infer_response.to_dict()).encode('utf-8'))

        try:
            self.minio_client.put_object(
                minio_bucket_name,
                f"{infer_response.id}.json",
                predictions,
                predictions.getbuffer().nbytes,
                content_type="application/json",
            )
        except Exception as e:
            print(f"Failure to upload predictions to {minio_bucket_name}: {e}")

        if "request-type" in headers and headers["request-type"] == "v1":
            if self.protocol == PredictorProtocol.REST_V1.value:
                return infer_response
            else:
                # if predictor protocol is v2 but transformer uses v1
                return {"predictions": infer_response.outputs[0].as_numpy().tolist()}
        else:
            return infer_response


parser = argparse.ArgumentParser(parents=[model_server.parser])
args, _ = parser.parse_known_args()

if __name__ == "__main__":
    if args.configure_logging:
        logging.configure_logging(args.log_config_file)
    model = SimpleTransformer(
        args.model_name,
        predictor_host=args.predictor_host,
        predictor_protocol=args.predictor_protocol,
        predictor_use_ssl=args.predictor_use_ssl,
        minio_client=get_minio_client(),
    )
    ModelServer().start([model])
