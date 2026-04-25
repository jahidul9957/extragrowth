#!/usr/bin/env bash
# exit on error
set -o errexit

# 📦 1. Python Libraries Install
pip install -r requirements.txt

# 🤖 2. Playwright Headless Browser Install
playwright install chromium

# 🎨 3. Collect Static Files
python manage.py collectstatic --no-input

# 🚀 4. THE BULLETPROOF MIGRATIONS (Force Core First)
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate

# 👑 5. DIRECT ADMIN CREATION
export DJANGO_SUPERUSER_USERNAME="admin"
export DJANGO_SUPERUSER_EMAIL="admin@gmail.com"
export DJANGO_SUPERUSER_PASSWORD="adminpass"

python manage.py createsuperuser --noinput || true
