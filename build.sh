#!/usr/bin/env bash
# exit on error
set -o errexit

# 📦 1. Python Libraries Install
pip install -r requirements.txt

# 🤖 2. Playwright Headless Browser Install
playwright install chromium

# 📁 3. Ensure Folder Exists
mkdir -p core/migrations
touch core/migrations/__init__.py

# 🧹 4. SAFE DB RESET
rm -f db.sqlite3
find core/migrations/ -type f -name "*.py" -not -name "__init__.py" -delete || true
find core/migrations/ -type f -name "*.pyc" -delete || true

# 🎨 5. Collect Static Files
python manage.py collectstatic --no-input

# 🚀 6. Fresh Database Migrations
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate

# 👑 7. DIRECT ADMIN CREATION
export DJANGO_SUPERUSER_USERNAME="admin"
export DJANGO_SUPERUSER_EMAIL="admin@gmail.com"
export DJANGO_SUPERUSER_PASSWORD="adminpass"

python manage.py createsuperuser --noinput || true
