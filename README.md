# Kserve inference for MinIO event

We assume that you have installed OpenShift AI operator.

## Configuring the data science cluster

The following command creates a data science cluster configuration that enables
or disables the features. This file Kserver and ModelMesh for single and multi
model inference services. The other features are disabled.

```bash
oc create -f deploy/datasciencecluster-default-dsc.yaml
```

## Deploying MinIO


```bash
oc create -f deploy/minio/namespace.yaml
```

```bash
oc create -f deploy/minio/configmap.yaml
oc create -f deploy/minio/secret.yaml
```

```bash
oc create -f deploy/minio/persistentvolumeclaim.yaml
```

```bash
oc create -f deploy/minio/deployment.yaml
```

```bash
oc create -f deploy/minio/service.yaml
```

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

