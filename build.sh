#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# 🧹 1. MASTER RESET: Purani Ghost Files aur Database ko delete karna
rm -f db.sqlite3
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete

# 🎨 2. Collect Static Files (Design ke liye)
python manage.py collectstatic --no-input

# 🚀 3. Fresh Database Migrations (Naya aur clean DB banana)
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate
