#!/usr/bin/env bash
# exit on error
set -o errexit

# 📦 1. Python Libraries Install
pip install -r requirements.txt

# 🤖 2. Playwright Headless Browser Install (Zaruri hai!)
playwright install chromium

# 📁 3. Ensure Folder Exists (Folder gayab hone se bachane ke liye)
mkdir -p core/migrations
touch core/migrations/__init__.py

# 🧹 4. SAFE DB RESET (Sirf apne app ka kachra saaf karna)
rm -f db.sqlite3
find core/migrations/ -type f -name "*.py" -not -name "__init__.py" -delete || true
find core/migrations/ -type f -name "*.pyc" -delete || true

# 🎨 5. Collect Static Files (Design ke liye)
python manage.py collectstatic --no-input

# 🚀 6. Fresh Database Migrations
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate

# 👑 7. DIRECT ADMIN CREATION (Bina Render Dashboard ke)
export DJANGO_SUPERUSER_USERNAME="admin"
export DJANGO_SUPERUSER_EMAIL="admin@gmail.com"
export DJANGO_SUPERUSER_PASSWORD="adminpass"

python manage.py createsuperuser --noinput || true
