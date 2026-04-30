#!/usr/bin/env bash
# exit on error
set -o errexit

echo "📦 1. Installing Libraries..."
pip install -r requirements.txt
pip install Pillow 

echo "🌐 2. Setting up Playwright..."
playwright install chromium

echo "🎨 3. Collecting Static Files..."
python manage.py collectstatic --no-input

echo "📂 4. Fixing Migrations Folder (The Secret Hack!)..."
# यह कमांड ज़बरदस्ती फोल्डर बनाएगी ताकि Django माइग्रेशन सेव कर सके!
mkdir -p core/migrations
touch core/migrations/__init__.py

echo "🗄️ 5. Making Migrations for CORE app..."
python manage.py makemigrations core
python manage.py makemigrations

echo "🚀 6. Applying Migrations to Database..."
python manage.py migrate --no-input

echo "👑 7. Creating Superuser..."
export DJANGO_SUPERUSER_PASSWORD="adminpass"
python manage.py createsuperuser --noinput --username admin --email admin@nextgen.com || true

echo "✅ ALL DONE SUCCESSFULLY!"
