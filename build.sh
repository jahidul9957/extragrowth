#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# 🧹 1. SAFE RESET: Sirf 'core' app ka kachra saaf karna
rm -f db.sqlite3
find core/migrations/ -type f -name "*.py" -not -name "__init__.py" -delete
find core/migrations/ -type f -name "*.pyc" -delete

# 🎨 2. Collect Static Files 
python manage.py collectstatic --no-input

# 🚀 3. Fresh Database Migrations
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate
