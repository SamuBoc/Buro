from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_PROFESOR, ROLE_SECRETARIA
from accounts.decorators import role_required
from accounts.permissions import can_manage_case_deadline, can_reassign_case, can_view_case

from .forms import CaseDeadlineForm, CaseForm, CaseReassignmentForm, CaseRejectionForm
from .models import Case, CaseAuditLog, CaseDocument, Notification
from .services import auto_assign_case, reassign_case


def _get_user_draft(user):
    return (
        Case.objects
        .filter(created_by=user, status=Case.STATUS_DRAFT)
        .order_by('-created_at', '-pk')
        .first()
    )


def _can_access_draft(user, case):
    return user.is_superuser or case.created_by_id == user.id


def _render_case_form(request, form, draft_case=None, is_editing_draft=False):
    return render(request, 'cases/case_register.html', {
        'form': form,
        'draft_case': draft_case,
        'is_editing_draft': is_editing_draft,
    })


def _build_deadline_priority(case, today):
    if not case.deadline_date:
        return {
            'text': 'Sin fecha limite',
            'days_remaining': None,
            'priority_label': 'Sin prioridad',
            'priority_class': 'priority-none',
            'deadline_class': 'deadline-none',
        }

    days_remaining = (case.deadline_date - today).days

    if days_remaining < 0:
        priority_label = 'Critica'
        priority_class = 'priority-critical'
        deadline_text = f'Vencido hace {abs(days_remaining)} dia(s)'
        deadline_class = 'deadline-overdue'
    elif days_remaining <= 2:
        priority_label = 'Alta'
        priority_class = 'priority-high'
        deadline_text = 'Vence hoy' if days_remaining == 0 else f'Vence en {days_remaining} dia(s)'
        deadline_class = 'deadline-soon'
    elif days_remaining <= 7:
        priority_label = 'Media'
        priority_class = 'priority-medium'
        deadline_text = f'Vence en {days_remaining} dia(s)'
        deadline_class = 'deadline-normal'
    else:
        priority_label = 'Baja'
        priority_class = 'priority-low'
        deadline_text = f'Vence en {days_remaining} dia(s)'
        deadline_class = 'deadline-normal'

    return {
        'text': deadline_text,
        'days_remaining': days_remaining,
        'priority_label': priority_label,
        'priority_class': priority_class,
        'deadline_class': deadline_class,
    }


@login_required
def case_list(request):
    today = timezone.localdate()
    cases = list(Case.objects.select_related('beneficiary', 'assigned_student').all())

    for case in cases:
        deadline_priority = _build_deadline_priority(case, today)
        case.deadline_status_text = deadline_priority['text']
        case.days_remaining = deadline_priority['days_remaining']
        case.priority_label = deadline_priority['priority_label']
        case.priority_class = deadline_priority['priority_class']
        case.deadline_class = deadline_priority['deadline_class']

    return render(request, 'cases/case_list.html', {
        'cases': cases,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def case_create(request):
    draft_case = _get_user_draft(request.user)

    if request.method == 'POST':
        submit_action = request.POST.get('submit_action', 'complete')
        is_draft_submission = submit_action == 'draft'
        form = CaseForm(
            request.POST,
            request.FILES,
            instance=draft_case,
            allow_partial=is_draft_submission,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    case = form.save(commit=False)
                    case.created_by = request.user
                    case._request = request
                    case.status = (
                        Case.STATUS_DRAFT
                        if is_draft_submission
                        else Case.STATUS_COMPLETE
                    )
                    case.save()

                    for document in form.cleaned_data.get('documents', []):
                        CaseDocument.objects.create(case=case, file=document)

                    student = None
                    if case.status == Case.STATUS_COMPLETE:
                        student = auto_assign_case(case)

                if is_draft_submission:
                    messages.success(
                        request,
                        f'Se guardo el borrador del caso {case.code}. Puedes continuarlo despues.'
                    )
                elif student is None:
                    messages.warning(
                        request,
                        f'El caso {case.code} fue registrado pero no hay estudiantes disponibles para asignarlo.'
                    )
                else:
                    messages.success(
                        request,
                        f'El caso {case.code} fue registrado y asignado a {student.get_full_name() or student.username}.'
                    )
                if is_draft_submission:
                    return redirect('case_create')
                return redirect('case_detail', pk=case.pk)
            except Exception:
                messages.error(
                    request,
                    'Ocurrio un problema al guardar el caso y sus documentos. Intente nuevamente.'
                )
        else:
            messages.error(request, 'Por favor corrija los errores del formulario.')
    else:
        form = CaseForm(instance=draft_case, allow_partial=bool(draft_case))
        if draft_case:
            messages.info(
                request,
                f'Tienes un borrador pendiente ({draft_case.code}). Puedes continuar completandolo.'
            )

    return _render_case_form(request, form, draft_case=draft_case)


@login_required
def case_draft_list(request):
    drafts = (
        Case.objects
        .filter(created_by=request.user, status=Case.STATUS_DRAFT)
        .select_related('beneficiary', 'assigned_student')
        .order_by('-created_at')
    )

    return render(request, 'cases/case_draft_list.html', {
        'drafts': drafts,
    })


@login_required
def case_edit_draft(request, pk):
    draft_case = get_object_or_404(
        Case.objects.select_related('beneficiary', 'assigned_student'),
        pk=pk,
        status=Case.STATUS_DRAFT,
    )

    if not _can_access_draft(request.user, draft_case):
        messages.error(request, 'No tienes permisos para editar este borrador.')
        return redirect('case_draft_list')

    if request.method == 'POST':
        submit_action = request.POST.get('submit_action', 'draft')
        is_draft_submission = submit_action == 'draft'
        form = CaseForm(
            request.POST,
            request.FILES,
            instance=draft_case,
            allow_partial=is_draft_submission,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    case = form.save(commit=False)
                    case.created_by = draft_case.created_by or request.user
                    case._request = request
                    case.status = (
                        Case.STATUS_DRAFT if is_draft_submission else Case.STATUS_COMPLETE
                    )
                    case.save()

                    for document in form.cleaned_data.get('documents', []):
                        CaseDocument.objects.create(case=case, file=document)

                    student = None
                    if case.status == Case.STATUS_COMPLETE:
                        student = auto_assign_case(case)

                if is_draft_submission:
                    messages.success(
                        request,
                        f'Se actualizo el borrador del caso {case.code}.'
                    )
                    return redirect('case_edit_draft', pk=case.pk)

                if student is None:
                    messages.warning(
                        request,
                        f'El caso {case.code} fue completado pero no hay estudiantes disponibles para asignarlo.'
                    )
                else:
                    messages.success(
                        request,
                        f'El caso {case.code} fue completado y asignado a {student.get_full_name() or student.username}.'
                    )
                return redirect('case_detail', pk=case.pk)
            except Exception:
                messages.error(
                    request,
                    'Ocurrio un problema al actualizar el borrador. Intente nuevamente.'
                )
        else:
            messages.error(request, 'Por favor corrija los errores del formulario.')
    else:
        form = CaseForm(instance=draft_case, allow_partial=True)

    return _render_case_form(
        request,
        form,
        draft_case=draft_case,
        is_editing_draft=True,
    )


@login_required
def case_detail(request, pk):
    case = get_object_or_404(
        Case.objects
        .select_related('beneficiary', 'assigned_student')
        .prefetch_related('documents', 'reassignment_logs__changed_by', 'reassignment_logs__old_student', 'reassignment_logs__new_student'),
        pk=pk
    )

    if not can_view_case(request.user, case):
        messages.error(request, 'No tienes permisos para acceder a este caso.')
        return redirect('case_list')

    return render(request, 'cases/case_detail.html', {
        'case': case,
        'can_reassign': can_reassign_case(request.user),
        'can_manage_deadline': can_manage_case_deadline(request.user),
        'deadline_form': CaseDeadlineForm(instance=case),
        'reassignment_form': CaseReassignmentForm(case=case),
        'rejection_form': CaseRejectionForm(instance=case),
    })


@role_required(ROLE_SECRETARIA, ROLE_PROFESOR, ROLE_ADMINISTRADOR)
def case_update_deadline(request, pk):
    case = get_object_or_404(
        Case.objects.select_related('beneficiary', 'assigned_student'),
        pk=pk
    )

    if request.method != 'POST':
        return redirect('case_detail', pk=case.pk)

    form = CaseDeadlineForm(request.POST, instance=case)

    if form.is_valid():
        deadline_case = form.save()
        messages.success(
            request,
            f'La fecha limite del caso {deadline_case.code} fue actualizada.'
        )
        return redirect('case_detail', pk=case.pk)

    return render(request, 'cases/case_detail.html', {
        'case': case,
        'can_reassign': can_reassign_case(request.user),
        'can_manage_deadline': can_manage_case_deadline(request.user),
        'deadline_form': form,
        'reassignment_form': CaseReassignmentForm(case=case),
        'rejection_form': CaseRejectionForm(instance=case),
    })


@role_required(ROLE_SECRETARIA, ROLE_PROFESOR, ROLE_ADMINISTRADOR)
def case_reassign(request, pk):
    case = get_object_or_404(
        Case.objects.select_related('beneficiary', 'assigned_student'),
        pk=pk
    )

    if request.method != 'POST':
        return redirect('case_detail', pk=case.pk)

    form = CaseReassignmentForm(request.POST, case=case)

    if form.is_valid():
        new_student = form.cleaned_data['assigned_student']
        old_student = reassign_case(case, new_student, request.user)
        previous_name = old_student.get_full_name() or old_student.username if old_student else 'Sin asignar'
        new_name = new_student.get_full_name() or new_student.username
        messages.success(
            request,
            f'El caso {case.code} fue reasignado de {previous_name} a {new_name}.'
        )
        return redirect('case_detail', pk=case.pk)

    messages.error(request, 'Por favor seleccione un estudiante valido.')
    return render(request, 'cases/case_detail.html', {
        'case': case,
        'can_reassign': can_reassign_case(request.user),
        'can_manage_deadline': can_manage_case_deadline(request.user),
        'deadline_form': CaseDeadlineForm(instance=case),
        'reassignment_form': form,
        'rejection_form': CaseRejectionForm(instance=case),
    })


@role_required(ROLE_SECRETARIA, ROLE_PROFESOR, ROLE_ADMINISTRADOR)
def case_reject(request, pk):
    case = get_object_or_404(
        Case.objects.select_related('beneficiary', 'assigned_student'),
        pk=pk
    )

    if request.method != 'POST':
        return redirect('case_detail', pk=case.pk)

    form = CaseRejectionForm(request.POST, instance=case)

    if form.is_valid():
        try:
            with transaction.atomic():
                case.state = Case.STATE_REJECTED
                case.rejection_reason = form.cleaned_data['rejection_reason']
                case._request = request
                case.save()

                messages.success(
                    request,
                    f'El caso {case.code} ha sido rechazado exitosamente.'
                )
        except Exception:
            messages.error(
                request,
                'Ocurrió un problema al rechazar el caso. Intente nuevamente.'
            )
        return redirect('case_detail', pk=case.pk)

    messages.error(request, 'Por favor ingrese una causal de rechazo válida.')
    return render(request, 'cases/case_detail.html', {
        'case': case,
        'can_reassign': can_reassign_case(request.user),
        'can_manage_deadline': can_manage_case_deadline(request.user),
        'deadline_form': CaseDeadlineForm(instance=case),
        'reassignment_form': CaseReassignmentForm(case=case),
        'rejection_form': form,
    })


@login_required
def case_audit_log(request, case_id):
    case = get_object_or_404(Case, pk=case_id)

    has_access = (
        request.user.is_staff
        or request.user.groups.filter(
            name__in=[ROLE_SECRETARIA, ROLE_PROFESOR, ROLE_ADMINISTRADOR]
        ).exists()
        or case.assigned_student == request.user
    )
    if not has_access:
        messages.error(request, 'No tienes permiso para ver la bitacora de este caso.')
        return redirect('case_list')

    logs = CaseAuditLog.objects.filter(case=case).select_related('user').order_by('-timestamp')

    return render(request, 'cases/case_audit_log.html', {
        'case': case,
        'logs': logs,
        'page_title': f'Bitacora - {case.code}',
    })


@login_required
def global_audit_log(request):
    if not (
        request.user.is_staff
        or request.user.groups.filter(name=ROLE_ADMINISTRADOR).exists()
    ):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('case_list')

    logs = CaseAuditLog.objects.select_related('user', 'case').order_by('-timestamp')[:500]
    return render(request, 'cases/global_audit_log.html', {
        'logs': logs,
        'page_title': 'Bitacora Global de Casos',
    })


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient_user=request.user
    ).select_related('case').order_by('-created_at')

    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'cases/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'page_title': 'Mis Notificaciones',
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient_user=request.user,
    )
    notification.mark_as_read()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'notification_id': notification_id})

    return redirect('case_detail', pk=notification.case_id)


@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(
            recipient_user=request.user,
            is_read=False,
        ).update(is_read=True, read_at=timezone.now())
        messages.success(request, 'Todas las notificaciones marcadas como leidas.')
    return redirect('notification_list')


@login_required
def unread_notifications_count(request):
    count = Notification.objects.filter(
        recipient_user=request.user,
        is_read=False,
    ).count()
    return JsonResponse({'unread_count': count})
