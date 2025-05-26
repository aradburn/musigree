.PHONY: install run-dev run-prod help

help:
	@echo "make install      Install dependencies"
	@echo "make run-dev      Run development server"
	@echo "make run-prod     Run production server"
	@echo "make help         Show this help message"

install:
	@echo "Installing dependencies..."
	pip install fastapi uvicorn jinja2 fakeredis sqlalchemy starlette python-multipart

run-dev:
	@echo "Starting development server..."
	python -m musigree.app.fastapi_dev_app

run-prod:
	@echo "Starting production server..."
	uvicorn musigree.app.fastapi_prod_app:app --host 0.0.0.0 --port 8000 --workers 4