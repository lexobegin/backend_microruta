# gunicorn.conf.py
import multiprocessing
import os

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Server socket
bind = "0.0.0.0:8000"

# Logging - crear directorios si no existen
os.makedirs("/var/log/gunicorn", exist_ok=True)
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process name
proc_name = "microruta_backend"

# Daemonize
daemonize = False