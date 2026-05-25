import os
import sys

proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model

U = get_user_model()
print('Total users:', U.objects.count())
print('Superusers:', [u.username for u in U.objects.filter(is_superuser=True)])
print('Users and groups:')
for u in U.objects.all():
    print(f"{u.username} -> {list(u.groups.values_list('name', flat=True))} (super={u.is_superuser})")
