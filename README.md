# Kubeflow pipeline for MinIO event

## Quick start

We assume that you have installed OpenShift AI and that you have created a
namespace to deploy the stack. In the follwing examples, the namespace is named
`myspace`. We also assume that you have a default storage class for the
persistent volumes.

For convenience, the configuration has been isolated in the
[deploy/config.yaml](deploy/config.yaml) file. You can set the MinIO credentials,
the MinIO bucket for the files that trigger the Kubeflow pipeline, and the
Kubeflow pipeline name to trigger. Simply modify the values to your needs, before
running the following command.

```bash
oc create -n myspace deploy/config.yaml
```

The following command creates a MinIO deployment with a single pod,
with a 20 GB persistent volume for the data. It uses service service
certificates for the TLS configuration on the internal network, and reencrypt
routes for external facing URLs.

```bash
oc create -n myspace deploy/minio.yaml
```

The following command creates the webhook that is called when files are created
in the bucket named `mybucket`. The bucket is created by the postStart command
if it does not exist and the event notification is also created. The even
notification configuration is removed when the webhook pod exits. Here again, a
service service certificate is used for TLS.

```bash
oc create -n myspace deploy/minio-webhook.yaml
```
