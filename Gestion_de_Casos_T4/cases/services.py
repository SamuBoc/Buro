from django.contrib.auth import get_user_model
from django.db.models import Count, F

from accounts.constants import ROLE_ESTUDIANTE
from .models import Case

User = get_user_model()


def get_available_student():
    return (
        User.objects
        .filter(is_active=True, groups__name=ROLE_ESTUDIANTE)
        .annotate(current_load=Count('assigned_cases'))
        .filter(current_load__lt=F('profile__max_cases'))
        .order_by('current_load', 'id')
        .first()
    )


def auto_assign_case(case):
    student = get_available_student()

    if student is None:
        case.state = Case.STATE_NO_STUDENTS
        case.assigned_student = None
    else:
        case.assigned_student = student
        case.state = Case.STATE_ASSIGNED

    case.save(update_fields=['assigned_student', 'state'])
    return student
