import os
import sys

proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django

django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils import timezone

from accounts.constants import ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary
from cases.models import Case


User = get_user_model()


def ensure_user(username, email, password, role):
    group, _ = Group.objects.get_or_create(name=role)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': email},
    )
    if created:
        user.set_password(password)
        user.save()
    user.groups.add(group)
    return user


profesor = ensure_user('profesor1', 'profesor1@correo.com', 'Prof1234!', ROLE_PROFESOR)
student1 = ensure_user('estudiante1', 'estudiante1@correo.com', 'Estu1234!', ROLE_ESTUDIANTE)
student2 = ensure_user('estudiante2', 'estudiante2@correo.com', 'Estu1234!', ROLE_ESTUDIANTE)

demo_emails = ['benef1@demo.com', 'benef2@demo.com']
Case.objects.filter(description__startswith='Caso demo').delete()
Beneficiary.objects.filter(email__in=demo_emails).delete()

beneficiary1 = Beneficiary.objects.create(
    name='Beneficiario Demo 1',
    location='Cali',
    phone='3000000001',
    email='benef1@demo.com',
)
beneficiary2 = Beneficiary.objects.create(
    name='Beneficiario Demo 2',
    location='Cali',
    phone='3000000002',
    email='benef2@demo.com',
)

Case.objects.create(
    sala=Case.ROOM_CIVIL,
    description='Caso demo civil',
    beneficiary=beneficiary1,
    created_by=profesor,
    assigned_student=student1,
    status=Case.STATUS_COMPLETE,
    state=Case.STATE_ASSIGNED,
)
Case.objects.create(
    sala=Case.ROOM_LABORAL,
    description='Caso demo laboral',
    beneficiary=beneficiary2,
    created_by=profesor,
    assigned_student=student1,
    status=Case.STATUS_COMPLETE,
    state=Case.STATE_ASSIGNED,
)
Case.objects.create(
    sala=Case.ROOM_FAMILIA,
    description='Caso demo familia',
    beneficiary=beneficiary2,
    created_by=profesor,
    assigned_student=student2,
    status=Case.STATUS_COMPLETE,
    state=Case.STATE_ASSIGNED,
)

print('Datos de prueba creados:')
print(' - Profesor: profesor1 / Prof1234!')
print(' - Estudiantes: estudiante1, estudiante2')
print(' - Casos asignados: 3')
