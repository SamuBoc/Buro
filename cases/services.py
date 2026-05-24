from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Case as DbCase, Count, F, IntegerField, Q, Value, When
from django.utils import timezone

from accounts.constants import (
    ROLE_ADMINISTRADOR,
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)

from .email_utils import send_deadline_alert_email
from .models import Case, CaseAuditLog, CaseReassignmentLog, Notification

User = get_user_model()


def get_academic_student_candidates(case=None):
    """
    Retorna estudiantes del modulo academico elegibles para asignacion.

    Criterios base:
    - pertenecer al grupo estudiante
    - tener perfil academico registrado (student_code)
    - estar activos y disponibles
    - no superar su carga maxima

    Priorizacion:
    - coincidencia entre sala del caso y sala preferente
    - menor carga actual
    - id mas bajo como desempate estable
    """
    preferred_room = getattr(case, 'sala', None)

    candidates = (
        User.objects
        .filter(
            is_active=True,
            groups__name=ROLE_ESTUDIANTE,
            profile__student_code__isnull=False,
            profile__availability=True,
        )
        .exclude(profile__student_code='')
        .select_related('profile')
        .annotate(
            current_load=Count(
                'assigned_cases',
                filter=~Q(assigned_cases__status=Case.STATUS_DRAFT),
                distinct=True,
            ),
            room_affinity=DbCase(
                When(profile__preferred_room=preferred_room, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        )
        .filter(current_load__lt=F('profile__max_cases'))
        .distinct()
    )

    return candidates.order_by('-room_affinity', 'current_load', 'id')


def get_available_student(case=None):
    return (
        get_academic_student_candidates(case)
        .first()
    )


def select_best_student_candidate(case):
    """
    Selecciona el mejor candidato academico para un caso usando:
    - disponibilidad
    - carga maxima
    - menor cantidad de casos activos
    - afinidad con la sala juridica
    """
    return get_available_student(case)


def _get_assignment_recipients(case, student):
    """Retorna lista de destinatarios para notificación de asignación."""
    recipients = []
    recipient_ids = set()

    if student and student.is_active:
        recipients.append(student)
        recipient_ids.add(student.id)

    staff_users = (
        User.objects.filter(
            is_active=True,
            groups__name__in=[ROLE_PROFESOR, ROLE_SECRETARIA, ROLE_ADMINISTRADOR],
        )
        .distinct()
        .order_by('id')
    )
    for user in staff_users:
        if user.id not in recipient_ids:
            recipients.append(user)
            recipient_ids.add(user.id)

    return recipients


def _notify_assignment(case, student):
    """Crea notificaciones ASSIGNMENT para el estudiante y profesores activos."""
    recipients = _get_assignment_recipients(case, student)
    for recipient in recipients:
        Notification.objects.create(
            recipient_user=recipient,
            case=case,
            notification_type='ASSIGNMENT',
            title=f'Caso {case.code} asignado',
            message=(
                f'El caso {case.code} '
                f'(Beneficiario: {case.beneficiary.name if case.beneficiary else "Sin beneficiario"}) '
                f'ha sido asignado a {student.get_full_name() or student.username}.'
            ),
        )


def _log_auto_assignment(case, student):
    """
    Registra en bitacora el resultado del proceso de asignacion automatica.
    """
    if student is None:
        CaseAuditLog.objects.create(
            case=case,
            user=None,
            action='UPDATED',
            description=(
                f'No fue posible asignar automaticamente el caso {case.code}. '
                'El caso permanece pendiente por falta de estudiantes disponibles '
                'o por capacidad academica insuficiente.'
            ),
            previous_status=Case.STATE_PENDING,
            new_status=case.state,
            case_radicado=case.code,
        )
        return

    CaseAuditLog.objects.create(
        case=case,
        user=None,
        action='ASSIGNED',
        description=(
            f'Asignacion automatica realizada para el caso {case.code}. '
            f'Estudiante seleccionado: {student.get_full_name() or student.username}. '
            f'Carga activa actual del estudiante: {student.profile.active_cases}.'
        ),
        previous_status=Case.STATE_PENDING,
        new_status=case.state,
        case_radicado=case.code,
    )


def auto_assign_case(case):
    student = select_best_student_candidate(case)
    if student is None:
        case.state = Case.STATE_NO_STUDENTS
        case.assigned_student = None
    else:
        case.assigned_student = student
        case.state = Case.STATE_ASSIGNED
    case._skip_status_log = True
    case.save(update_fields=['assigned_student', 'state'])

    _log_auto_assignment(case, student)

    if student is not None:
        _notify_assignment(case, student)

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
        old_name = (
            old_student.get_full_name() or old_student.username
            if old_student else 'Sin asignar'
        )
        new_name = (
            new_student.get_full_name() or new_student.username
            if new_student else 'Sin asignar'
        )
        CaseAuditLog.objects.create(
            case=case,
            user=changed_by,
            action='REASSIGNED',
            description=(
                f'El caso {case.code} fue reasignado de {old_name} a {new_name} '
                f'por {changed_by.get_full_name() or changed_by.username}.'
            ),
            previous_status=Case.STATE_ASSIGNED,
            new_status=case.state,
            case_radicado=case.code,
        )

    _notify_assignment(case, new_student)

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
    today       = reference_date or timezone.localdate()
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
            notification = Notification.objects.create(
                recipient_user=recipient,
                case=case,
                notification_type='DEADLINE',
                title=f'Caso {case.code} vence el {case.deadline_date:%d/%m/%Y}',
                message=(
                    f'El caso {case.code} tiene fecha limite de atencion el '
                    f'{case.deadline_date:%d/%m/%Y}. '
                    f'Restan {days_remaining} dia(s) para su vencimiento.'
                ),
            )
            send_deadline_alert_email(notification)
            created_notifications += 1

        case.deadline_alert_sent_at = timezone.now()
        case.save(update_fields=['deadline_alert_sent_at'])

    return created_notifications