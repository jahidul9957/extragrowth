#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# 📁 1. Ensure Folder Exists (Taki script crash na ho)
mkdir -p core/migrations
touch core/migrations/__init__.py

# 🧹 2. SAFE RESET (Agar file nahi hai toh ignore karo '|| true')
rm -f db.sqlite3
find core/migrations/ -type f -name "*.py" -not -name "__init__.py" -delete || true
find core/migrations/ -type f -name "*.pyc" -delete || true

# 🎨 3. Collect Static Files 
python manage.py collectstatic --no-input

# 🚀 4. Fresh Database Migrations
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate
