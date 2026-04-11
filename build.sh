#!/usr/bin/env bash
# Salir si hay algún error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate


python manage.py createsuperuser --noinput --username Alejandro --email alejandro.nu.rdz@gmail.com || true