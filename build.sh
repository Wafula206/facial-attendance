#!/bin/bash

echo "===== Attendance System Build Script ====="

# Install dependencies
pip install -r requirements.txt

# Navigate to backend
cd backend

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if not exists
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@attendance.com', 'Admin123!')
    print('Superuser created: admin / Admin123!')
else:
    print('Superuser already exists')
"

echo "===== Build Complete ====="
