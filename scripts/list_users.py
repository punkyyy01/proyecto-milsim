import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_milsim.settings')
import django
django.setup()

from django.contrib.auth.models import User

for u in User.objects.all():
    print(u.username)
