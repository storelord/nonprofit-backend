#!/bin/bash
source /var/www/nonprofit-backend/venv/bin/activate
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
