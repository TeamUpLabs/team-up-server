import multiprocessing

# Server socket configurations
bind = "0.0.0.0:8000"  # IP와 포트 설정
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # 적절한 워커 수 설정
worker_class = "uvicorn.workers.UvicornWorker"  # Use Uvicorn's worker for ASGI support
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = "team-up-server"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None

# Logging
loglevel = "info"
accesslog = "-"  # stdout
errorlog = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' 