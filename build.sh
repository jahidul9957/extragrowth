#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Libraries install करना
pip install -r requirements.txt

# 2. Playwright सेटअप (अगर इस्तेमाल कर रहे हैं)
playwright install chromium

# 3. Static files इकट्ठा करना
python manage.py collectstatic --no-input

# 🚀 4. डेटाबेस फिक्स (Free Users के लिए असली तरीका)
# ये कमांड्स हर बार बिल्ड के दौरान चलेंगी और एरर खत्म कर देंगी
python manage.py makemigrations core
python manage.py makemigrations
python manage.py migrate --no-input

# 5. Superuser बनाना (अगर पहली बार है)
# अगर admin पहले से है, तो ये लाइन एरर नहीं देगी (|| true की वजह से)
export DJANGO_SUPERUSER_PASSWORD="adminpass"
python manage.py createsuperuser --noinput --username admin --email admin@gmail.com || true
