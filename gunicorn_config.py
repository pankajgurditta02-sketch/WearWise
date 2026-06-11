bind = "0.0.0.0:8080"
workers = 2
worker_class = "sync"
timeout = 120
max_requests = 1000
max_requests_jitter = 100
graceful_timeout = 30
keepalive = 5
