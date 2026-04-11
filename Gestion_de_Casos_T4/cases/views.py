from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from accounts.decorators import role_required
from accounts.permissions import can_view_case

from .forms import CaseForm
from .models import Case, CaseDocument
from .services import auto_assign_case


@login_required
def case_list(request):
    cases = Case.objects.select_related('beneficiary', 'assigned_student').all()
    return render(request, 'cases/case_list.html', {
        'cases': cases,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def case_create(request):
    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    case = form.save()
                    for document in form.cleaned_data['documents']:
                        CaseDocument.objects.create(case=case, file=document)
                    student = auto_assign_case(case)

                if student is None:
                    messages.warning(
                        request,
                        f'El caso {case.code} fue registrado pero no hay estudiantes disponibles para asignarlo.'
                    )
                else:
                    messages.success(
                        request,
                        f'El caso {case.code} fue registrado y asignado a {student.get_full_name() or student.username}.'
                    )
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


@login_required
def case_detail(request, pk):
    case = get_object_or_404(
        Case.objects
        .select_related('beneficiary', 'assigned_student')
        .prefetch_related('documents'),
        pk=pk
    )

    if not can_view_case(request.user, case):
        messages.error(request, 'No tienes permisos para acceder a este caso.')
        return redirect('case_list')

    return render(request, 'cases/case_detail.html', {
        'case': case,
    })
