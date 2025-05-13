# Kserve inference for MinIO event

We assume that you have installed OpenShift AI operator.
We also assume that you have a default storage class for the persistent
volumes.

## Configuring the data science cluster

The following command creates a data science cluster configuration that enables
or disables the features. The current configuration enables Kserve and
ModelMesh for single and multi model inference services. The other features are
disabled.

```bash
oc create -f deploy/datasciencecluster-default-dsc.yaml
```

## Deploying MinIO

MinIO provides an S3-compatible storage backend that is used for the models and
the files ingested by our predictive model. We start by creating a namespace
named `minio`.

```bash
oc create -f deploy/minio/namespace.yaml
```

Then, we create a Secret with the minio credentials that will be used to set
the root username and password. You should modify the values in your
environement.

```bash
oc create -f deploy/minio/secret-minio-credentials.yaml
```

We also create a ConfigMap with the webhook for the data ingestion bucket. We
point it to our inference service transformer that will download the file and
pass it to the predictor.

```bash
oc create -f deploy/minio/configmap.yaml
```

We create the PersistentVolumeClaim to allocate storage for our buckets. For
simplicity, we use a single volume for all the buckets, but we could split them
for stronger data isolation.

You should adjust the size to allow storing all your data.

```bash
oc create -f deploy/minio/persistentvolumeclaim.yaml
```

For MinIO to be reachable by other pods with a comprehensive hostname, we
create services for the API and UI endpoints exposed by the container.
The service URL for the API is `https://minio.minio.svc:9000`.

The service is annotated with
`service.beta.openshift.io/serving-cert-secret-name: minio-tls` which triggers
the creation of a service serving certificate stored in the `minio-tls` secret.
The key and certificate are used by the pod, so we create the service first.

```bash
oc create -f deploy/minio/service.yaml
```

Now that all prerequisites have been set up, we deploy the MinIO pod.

```bash
oc create -f deploy/minio/deployment.yaml
```

Optionally, we deploy a route to make the services available externally.

```bash
oc create -f deploy/minio/route.yaml
```

## Upload the model



## Deploy the inference service

```bash
oc create -f deploy/edge-ai-app/namespace.yaml
```

```bash
oc create -f deploy/edge-ai-app/configmap-minio-config.yaml
```

```bash
oc create -f deploy/edge-ai-app/secret-storage-config.yaml
oc create -f deploy/edge-ai-app/secret-minio-credentials.yaml
```

```bash
oc create -f deploy/edge-ai-app/persistentvolumeclaim.yaml
```

```bash
oc create -f deploy/edge-ai-app/serviceaccount-yolo.yaml
```

```bash
oc create -f deploy/edge-ai-app/servingruntime-ovms.yaml
```

```bash
oc create -f deploy/edge-ai-app/inferenceservice-yolo.yaml
```

