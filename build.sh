#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install all libraries from requirements.txt
pip install -r requirements.txt

# 2. Collect Static Files (CSS, JS, Images)
# Yeh aapke Glassmorphism design ko live karne ke liye zaruri hai
python manage.py collectstatic --no-input

# 3. Database Updates
# Jab bhi models.py mein badlav karenge, yeh commands zaruri hain
python manage.py makemigrations
python manage.py migrate
