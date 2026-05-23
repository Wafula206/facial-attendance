import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Create admin user if it doesn't exist
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@attendance.com',
        password='Admin123!'
    )
    print('✅ Superuser created: admin / Admin123!')
else:
    print('✅ Superuser already exists')
