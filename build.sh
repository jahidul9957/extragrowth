#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Zaroori packages install karein
pip install -r requirements.txt

# 2. Database ki tables banayein (Yeh sabse zaroori hai!)
python manage.py makemigrations
python manage.py migrate

# 3. Apna Admin account banayein
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_PASSWORD=adminpass
export DJANGO_SUPERUSER_EMAIL=admin@admin.com
python manage.py createsuperuser --noinput || true
