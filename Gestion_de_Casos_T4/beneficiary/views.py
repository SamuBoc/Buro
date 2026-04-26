from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from accounts.decorators import role_required

from .forms import BeneficiaryForm, DocumentBeneficiaryForm, Update_Beneficiary_Form
from .models import Beneficiary, BeneficiaryAuditLog, DocumentBeneficiary


@login_required
def beneficiary_list(request):
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'beneficiary/beneficiary_list.html', {
        'beneficiaries': beneficiaries
    })


"""
Allow register a new benefeciary with all the data neccessary to save it in DataBase.
This function have a restriction role that only allow 'Secretaria' and 'Administrador'
add a new beneficiary.

If one of the allow roles will send the register beneficiary form, function make validation
of the form (No empty files, avaible char...). If ones fields are wrong, system will make a 
request to user about fix this mistake.
"""
@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def beneficiary_register(request):
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST)
        doc_form = DocumentBeneficiaryForm(request.POST, request.FILES)

        if form.is_valid() and doc_form.is_valid():
            beneficiary = form.save(commit=False)
            beneficiary._request = request
            beneficiary.save()

            documento = doc_form.save(commit=False)
            documento.beneficiary = beneficiary
            documento.save()

            return redirect('beneficiary_list')
        else:
            print(form.errors)
            print(doc_form.errors)
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = BeneficiaryForm()
        doc_form = DocumentBeneficiaryForm()

    return render(request, 'beneficiary/beneficiary_register.html', {
        'form': form,
        'doc_form': doc_form,
    })


"""
Roles 'Secretaria' or 'Administrador' could update/modify a register beneficiary.
"""
@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def beneficiary_update(request, pk):

    beneficiary = get_object_or_404(Beneficiary, pk=pk)

    saved_document = DocumentBeneficiary.objects.filter(beneficiary=beneficiary).first()

    if request.method == 'POST':
        form = Update_Beneficiary_Form(request.POST, instance=beneficiary)
        doc_form = DocumentBeneficiaryForm(request.POST, request.FILES, instance=saved_document)

        if form.is_valid():
            form.save()

            if request.FILES.get('file'):
                documento = doc_form.save(commit=False)
                documento.beneficiary = beneficiary
                documento.save()

            messages.success(request, 'Beneficiario actualizado exitosamente.')
            return redirect('beneficiary_list')
        else:
            print(form.errors)
            messages.error(request, "Corrige los errores del formulario")

    else:
        form = Update_Beneficiary_Form(instance=beneficiary)
        doc_form = DocumentBeneficiaryForm(instance=saved_document)

    return render(request, 'beneficiary/beneficiary_update.html', {
        'form': form,
        'doc_form': doc_form,
        'documento_existente': saved_document,
    })


@login_required
def beneficiary_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    documento = DocumentBeneficiary.objects.filter(beneficiary=beneficiary).first()
    return render(request, 'beneficiary/beneficiary_detail.html', {
        'beneficiary': beneficiary,
        'documento': documento,
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
