import os

workers = int(os.getenv('GUNICORN_PROCESSES', '2'))
threads = int(os.getenv('GUNICORN_THREADS', '4'))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '120'))
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8443')

forwarded_allow_ips = '*'

secure_scheme_headers = {'X-Forwarded-Proto': 'https'}
tls_secret_name = os.getenv('TLS_SECRET_NAME', None)
if not tls_secret_name:
    raise ('TLS_SECRET_NAME environment variable is not set')

keyfile = f"/var/run/secrets/{tls_secret_name}/tls.key"
certfile = f"/var/run/secrets/{tls_secret_name}/tls.crt"
ca_certs = f"/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt"
