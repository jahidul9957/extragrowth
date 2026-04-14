#!/usr/bin/env bash
set -o errexit

# 1. Packages install karein
pip install -r requirements.txt

# 2. Database tables banayein (Yahan 'core' likhna zaroori hai)
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate

# 3. Admin account banayein
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=adminpass
export DJANGO_SUPERUSER_EMAIL=admin@admin.com
python manage.py createsuperuser --noinput || true
