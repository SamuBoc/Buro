from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CaseForm
from .models import Case, CaseDocument


SECRETARIA_GROUP = 'secretaria'
ESTUDIANTE_GROUP = 'estudiante'
PROFESOR_GROUP = 'profesor'


def user_belongs_to_group(user, group_name):
    """Retorna True si el usuario pertenece al grupo indicado."""
    return user.groups.filter(name=group_name).exists()


def user_can_view_case(user, case):
    """Evalua si el usuario autenticado puede acceder al detalle del caso."""
    if user.is_superuser:
        return True

    if user_belongs_to_group(user, SECRETARIA_GROUP):
        return True

    if user_belongs_to_group(user, PROFESOR_GROUP):
        return True

    if user_belongs_to_group(user, ESTUDIANTE_GROUP) and case.assigned_student_id == user.id:
        return True

    return False


def case_list(request):
    """Lista los casos juridicos registrados."""
    cases = Case.objects.select_related('beneficiary', 'assigned_student').all()
    return render(request, 'cases/case_list.html', {
        'cases': cases,
    })


def case_create(request):
    """Registra un nuevo caso juridico junto con sus documentos."""
    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    case = form.save()
                    for document in form.cleaned_data['documents']:
                        CaseDocument.objects.create(case=case, file=document)

                messages.success(request, f'El caso {case.code} fue registrado exitosamente.')
                return redirect('case_detail', pk=case.pk)
            except Exception:
                messages.error(
                    request,
                    'Ocurrio un problema al guardar el caso y sus documentos. Intente nuevamente.'
                )
        else:
            messages.error(request, 'Por favor corrija los errores del formulario.')
    else:
        form = CaseForm()

    return render(request, 'cases/case_register.html', {
        'form': form,
    })


@login_required(login_url='admin:login')
def case_detail(request, pk):
    """Muestra el detalle de un caso juridico y sus documentos asociados."""
    case = get_object_or_404(
        Case.objects.select_related('beneficiary', 'assigned_student').prefetch_related('documents'),
        pk=pk
    )

    if not user_can_view_case(request.user, case):
        messages.error(request, 'No tienes permisos para acceder a este caso.')
        return redirect('case_list')

    return render(request, 'cases/case_detail.html', {
        'case': case,
    })

from .models import Case, CaseAuditLog

@login_required
def case_audit_log(request, case_id):
    case = get_object_or_404(Case, pk=case_id)

    user = request.user
    has_access = (
        user.is_staff
        or user.groups.filter(name__in=['Secretaria', 'Profesor', 'Administrador']).exists()
        or (hasattr(case, 'assigned_student') and case.assigned_student == user)
    )
    if not has_access:
        messages.error(request, 'No tienes permiso para ver la bitácora de este caso.')
        return redirect('cases:case_list')

    logs = CaseAuditLog.objects.filter(case=case).select_related('user').order_by('-timestamp')

    return render(request, 'cases/case_audit_log.html', {
        'case':       case,
        'logs':       logs,
        'page_title': f'Bitácora — {case.radicado}',
    })


@login_required
def global_audit_log(request):
    if not (request.user.is_staff or request.user.groups.filter(name='Administrador').exists()):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('cases:case_list')

    logs = CaseAuditLog.objects.select_related('user', 'case').order_by('-timestamp')[:500]
    return render(request, 'cases/global_audit_log.html', {
        'logs':       logs,
        'page_title': 'Bitácora Global de Casos',
    })