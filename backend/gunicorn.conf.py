import multiprocessing

# Workers: (2 x CPU cores) + 1 is the standard recommendation
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"

bind = "0.0.0.0:8000"
timeout = 120  # seconds before killing a hung worker (LLM calls can be slow)
graceful_timeout = 30  # seconds to wait for in-flight requests on SIGTERM
keepalive = 5  # seconds to keep idle connections open

# Logging
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = "info"

# Restart workers after this many requests to reclaim memory
max_requests = 1000
max_requests_jitter = 100  # randomise so workers don't restart simultaneously
