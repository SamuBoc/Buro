import os
import sys

proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

U = get_user_model()

users = [
    ('secretaria1', 'secretaria1@correo.com', 'Cambiar123!', 'secretaria'),
    ('profesor1', 'profesor1@correo.com', 'Prof1234!', 'profesor'),
    ('estudiante1', 'estudiante1@correo.com', 'Estu1234!', 'estudiante'),
    ('estudiante2', 'estudiante2@correo.com', 'Estu1234!', 'estudiante'),
]

for _u, _e, _p, gname in users:
    Group.objects.get_or_create(name=gname)

created = []
for username, email, password, gname in users:
    U.objects.filter(username=username).delete()
    user = U.objects.create_user(username=username, email=email, password=password)
    grp = Group.objects.get(name=gname)
    user.groups.add(grp)
    created.append((username, password, gname))

print('Usuarios creados:')
for u, p, g in created:
    print(f' - {u} ({g}) contraseña: {p}')
