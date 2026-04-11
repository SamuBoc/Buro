from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CaseForm
from .models import Case, CaseDocument


def case_list(request):
    """Lista los casos juridicos registrados."""
    cases = Case.objects.select_related('beneficiary').all()
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


def case_detail(request, pk):
    """Muestra el detalle de un caso juridico y sus documentos asociados."""
    case = get_object_or_404(
        Case.objects.select_related('beneficiary').prefetch_related('documents'),
        pk=pk
    )
    return render(request, 'cases/case_detail.html', {
        'case': case,
    })
