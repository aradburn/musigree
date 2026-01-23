#!/bin/sh
uv run gunicorn --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000 \
                --worker-connections 1000 --timeout 120 --keep-alive 5 \
                --max-requests 1000 --max-requests-jitter 100 --graceful-timeout 30 \
                --access-logfile - --error-logfile - --log-level info \
                 musigree.app.fastapi_prod_app:app