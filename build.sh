#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
# Apna superuser banane ka code
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=adminpass
export DJANGO_SUPERUSER_EMAIL=admin@admin.com
python manage.py createsuperuser --noinput || true
