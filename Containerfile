FROM registry.access.redhat.com/ubi9/ubi-minimal:9.5

RUN microdnf install -y python3.12 python3.12-pip && \
    microdnf clean all && \
    pip3.12 install flask gunicorn kfp minio requests


COPY app /app
COPY gunicorn_config.py /app/gunicorn_config.py

WORKDIR /app
USER 1000

EXPOSE 8080

CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
