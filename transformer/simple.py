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
import sys
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

def get_input_tensor_from_minio(record):
    """retrieves the numpy array input file from minio and return it
    Args:
        record: minio webhook file record
    Returns:
        numpy.array: Returns the numpy array as loaded from the file
    """
    minio_endpoint = os.getenv('MINIO_ENDPOINT')
    minio_username = os.getenv('MINIO_USERNAME')
    minio_password = os.getenv('MINIO_PASSWORD')
    minio_bucket_name = os.getenv('MINIO_BUCKET_NAME')

    print(f"Creating MinIO client for {minio_endpoint}")
    client = Minio(
        minio_endpoint,
        access_key=minio_username,
        secret_key=minio_password,
        http_client=urllib3.poolmanager.PoolManager(
            ca_certs='/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt',
        ),
    )

    filename = record['s3']['object']['key']
    print(f"Retrieving {filename} from {minio_bucket_name}")
    filepath = f"/data/{filename}"
    try:
        minio_object = client.fget_object(minio_bucket_name, filename, filepath)
    except Exception as e:
        print(f"Failure to get object: {filename}: {e}")

    input_tensor = np.load(filepath, allow_pickle=True)
    input_tensor_avg = np.average(input_tensor[:])
    input_tensor /= input_tensor_avg

    print(f"Deleting temporary file {filepath}")
    os.remove(filepath)

    return input_tensor


class ImageTransformer(Model):
    def __init__(
        self,
        name: str,
        predictor_host: str,
        predictor_protocol: str,
        predictor_use_ssl: bool,
    ):
        super().__init__(
            name,
            PredictorConfig(predictor_host, predictor_protocol, predictor_use_ssl),
            return_response_headers=True,
        )
        print(f"Predictor host: {predictor_host}")
        print(f"Predictor protocol: {predictor_protocol}")
        print(f"Predictor SSL: {predictor_use_ssl}")
        self.ready = True

    def preprocess(
        self, payload: Union[Dict, InferRequest], headers: Dict[str, str] = None
    ) -> Union[Dict, InferRequest]:
        if isinstance(payload, InferRequest):
            input_tensors = [
                image_transform(self.name, instance)
                for instance in payload.inputs[0].data
            ]
        else:
            headers["request-type"] = "v1"
            print(f"Request content: {json.dumps(payload)}")
            # Input follows the Tensorflow V1 HTTP API for binary values
            # https://www.tensorflow.org/tfx/serving/api_rest#encoding_binary_values
            input_tensors = [
                get_input_tensor_from_minio(record)
                for record in payload["Records"]
            ]
        input_tensors = np.asarray(input_tensors)
        infer_inputs = [
            InferInput(
                name="INPUT__0",
                datatype="FP32",
                shape=list(input_tensors.shape),
                data=input_tensors,
            )
        ]
        infer_request = InferRequest(model_name=self.name, infer_inputs=infer_inputs)

        # Transform to KServe v1/v2 inference protocol
        print(f"Protocol: {self.protocol}")
        if self.protocol == PredictorProtocol.REST_V1.value:
            inputs = [{"data": input_tensor.tolist()} for input_tensor in input_tensors]
            payload = {"instances": inputs}
            print(f"Payload: {json.dumps(payload)}")
            return payload
        else:
            return infer_request

    def postprocess(
        self,
        infer_response: Union[Dict, InferResponse],
        headers: Dict[str, str] = None,
        response_headers: Dict[str, str] = None,
    ) -> Union[Dict, InferResponse]:
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
print(f"Args: {args}")

if __name__ == "__main__":
    if args.configure_logging:
        logging.configure_logging(args.log_config_file)
    model = ImageTransformer(
        args.model_name,
        predictor_host=args.predictor_host,
        predictor_protocol=args.predictor_protocol,
        predictor_use_ssl=args.predictor_use_ssl,
    )
    ModelServer().start([model])
