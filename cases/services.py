from datetime import timedelta

from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, F
from django.utils import timezone

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_PROFESOR, ROLE_SECRETARIA
from accounts.constants import ROLE_ESTUDIANTE
from .models import Case, CaseReassignmentLog, Notification

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


def get_deadline_recipients(case):
    recipients = []

    if case.assigned_student and case.assigned_student.is_active:
        recipients.append(case.assigned_student)

    staff_users = (
        User.objects.filter(
            is_active=True,
            groups__name__in=[ROLE_SECRETARIA, ROLE_PROFESOR, ROLE_ADMINISTRADOR],
        )
        .distinct()
        .order_by('id')
    )

    recipient_ids = {user.id for user in recipients}
    for user in staff_users:
        if user.id not in recipient_ids:
            recipients.append(user)
            recipient_ids.add(user.id)

    return recipients


def generate_deadline_alerts(days_ahead=3, reference_date=None):
    today = reference_date or timezone.localdate()
    alert_limit = today + timedelta(days=days_ahead)
    cases = (
        Case.objects.select_related('beneficiary', 'assigned_student')
        .filter(
            deadline_date__isnull=False,
            deadline_date__gte=today,
            deadline_date__lte=alert_limit,
            deadline_alert_sent_at__isnull=True,
        )
        .order_by('deadline_date', 'id')
    )

    created_notifications = 0

    for case in cases:
        recipients = get_deadline_recipients(case)
        if not recipients:
            continue

        days_remaining = (case.deadline_date - today).days
        for recipient in recipients:
            Notification.objects.create(
                recipient_user=recipient,
                case=case,
                notification_type='DEADLINE',
                title=f'Caso {case.code} vence el {case.deadline_date:%d/%m/%Y}',
                message=(
                    f'El caso {case.code} tiene fecha limite de atencion el {case.deadline_date:%d/%m/%Y}. '
                    f'Restan {days_remaining} dias para su vencimiento.'
                ),
            )
            created_notifications += 1

        case.deadline_alert_sent_at = timezone.now()
        case.save(update_fields=['deadline_alert_sent_at'])

    return created_notifications
