#!/bin/sh
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000 --worker-connections 1000 musigree.app.fastapi_prod_app:app