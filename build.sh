#!/usr/bin/env bash
# exit on error (अगर कोई एरर आया तो बिल्ड रुक जाएगा)
set -o errexit

echo "📦 1. Installing Libraries..."
pip install -r requirements.txt
# (अगर requirements.txt में Pillow नहीं है, तो ये लाइन उसे इंस्टॉल कर देगी)
pip install Pillow 

echo "🌐 2. Setting up Playwright..."
playwright install chromium

echo "🎨 3. Collecting Static Files..."
python manage.py collectstatic --no-input

echo "🗄️ 4. Making Migrations for CORE app..."
# यह कमांड आपके डेटाबेस के लिए नई पर्ची (Migration File) बनाएगी
python manage.py makemigrations core
python manage.py makemigrations

echo "🚀 5. Applying Migrations..."
# यह कमांड उस पर्ची को Neon SQL में सेव कर देगी (जिससे profile_image वाला एरर खत्म होगा)
python manage.py migrate --no-input

echo "👑 6. Creating Superuser (If not exists)..."
export DJANGO_SUPERUSER_PASSWORD="adminpass"
python manage.py createsuperuser --noinput --username admin --email admin@nextgen.com || true

echo "✅ ALL DONE SUCCESSFULLY!"
