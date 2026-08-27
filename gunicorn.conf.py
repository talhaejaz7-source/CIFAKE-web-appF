import os

# Optimize Gunicorn for Render Free Tier (512MB RAM limit)
# Limit to exactly 1 worker and 1 thread to prevent memory overload and constant container crashes
workers = 1
threads = 1
timeout = 120
bind = "0.0.0.0:" + os.environ.get("PORT", "10000")
keepalive = 2
