#!/bin/bash

uv run -m memray run --live ../../wsgi.py
# uv run -m memray run -o memray-output.bin ../../wsgi.py