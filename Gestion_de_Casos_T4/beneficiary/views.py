from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from accounts.decorators import role_required

from .forms import BeneficiaryForm
from .models import Beneficiary, BeneficiaryAuditLog


@login_required
def beneficiary_list(request):
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'beneficiary/beneficiary_list.html', {
        'beneficiaries': beneficiaries
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def beneficiary_register(request):
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST)
        if form.is_valid():
            beneficiary = form.save(commit=False)
            beneficiary._request = request
            beneficiary.save()
            messages.success(request, 'Beneficiario registrado exitosamente.')
            return redirect('beneficiary_list')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = BeneficiaryForm()

    return render(request, 'beneficiary/beneficiary_register.html', {
        'form': form
    })


@login_required
def beneficiary_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    return render(request, 'beneficiary/beneficiary_detail.html', {
        'beneficiary': beneficiary
    })


@login_required
def beneficiary_audit_log(request, beneficiary_id):
    user = request.user
    has_access = (
        user.is_staff
        or user.groups.filter(name__in=[ROLE_SECRETARIA, ROLE_ADMINISTRADOR]).exists()
    )
    if not has_access:
        messages.error(request, 'No tienes permiso para ver esta bitácora.')
        return redirect('beneficiary_list')

    beneficiary = get_object_or_404(Beneficiary, pk=beneficiary_id)
    logs = BeneficiaryAuditLog.objects.filter(
        beneficiary=beneficiary
    ).select_related('user').order_by('-timestamp')

    return render(request, 'beneficiary/beneficiary_audit_log.html', {
        'beneficiary': beneficiary,
        'logs':        logs,
        'page_title':  f'Bitácora — {beneficiary.name}',
    })


@login_required
def global_beneficiary_audit_log(request):
    if not (request.user.is_staff or request.user.groups.filter(name=ROLE_ADMINISTRADOR).exists()):
        messages.error(request, 'Acceso restringido a administradores.')
        return redirect('beneficiary_list')

    logs = BeneficiaryAuditLog.objects.select_related(
        'user', 'beneficiary'
    ).order_by('-timestamp')[:500]

    return render(request, 'beneficiary/global_beneficiary_audit_log.html', {
        'logs':       logs,
        'page_title': 'Bitácora Global de Datos Personales',
    })