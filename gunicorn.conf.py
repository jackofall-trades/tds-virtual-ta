import os

# Use PORT environment variable for Render, default to 10000 for local development
port = int(os.environ.get('PORT', 10000))
bind = f"0.0.0.0:{port}"
workers = 2
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100 