from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, F

from accounts.constants import ROLE_ESTUDIANTE
from .models import Case, CaseReassignmentLog

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


def reassign_case(case, new_student, changed_by):
    old_student = case.assigned_student
    case.assigned_student = new_student
    case.state = Case.STATE_ASSIGNED

    with transaction.atomic():
        case.save(update_fields=['assigned_student', 'state'])
        CaseReassignmentLog.objects.create(
            case=case,
            old_student=old_student,
            new_student=new_student,
            changed_by=changed_by,
        )

    return old_student
