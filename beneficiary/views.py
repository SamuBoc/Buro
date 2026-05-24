from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from accounts.decorators import role_required

from .forms import (
    BeneficiaryForm,
    DataDeletionRequestForm,
    DocumentBeneficiaryForm,
    UpdateBeneficiaryForm,
)
from .models import (
    Beneficiary,
    BeneficiaryAuditLog,
    DataDeletionRequest,
    DocumentBeneficiary,
)

# Module that send mail notifications to beneficiaries
from mail import views


@login_required
def notify_beneficiary(request, pk):
    """
    Compatibilidad para la ruta legacy de notificacion por correo.
    La logica real vive en mail.views.notify_beneficiary; aqui solo evitamos
    que el enrutamiento falle al arrancar el servidor.
    """
    messages.info(request, 'Notificacion preparada.')
    return redirect('beneficiary_detail', pk=pk)


@login_required
def beneficiary_list(request):
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'beneficiary/beneficiary_list.html', {
        'beneficiaries': beneficiaries,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def beneficiary_register(request):
    if request.method == 'POST':
        form     = BeneficiaryForm(request.POST)
        doc_form = DocumentBeneficiaryForm(request.POST, request.FILES)

        if form.is_valid() and doc_form.is_valid():
            beneficiary          = form.save(commit=False)
            beneficiary._request = request
            beneficiary.save()

            documento             = doc_form.save(commit=False)
            documento.beneficiary = beneficiary
            documento.save()

            views.notify_beneficiary(beneficiary.id, "Registro Exitoso - Buro Juridico ICESI",
                               beneficiary.name + " usted a sido registrado exitosamente en la plataforma del Buro Juridíco de Icesi")

            return redirect('beneficiary_list')

        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form     = BeneficiaryForm()
        doc_form = DocumentBeneficiaryForm()

    return render(request, 'beneficiary/beneficiary_register.html', {
        'form':     form,
        'doc_form': doc_form,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def beneficiary_update(request, pk):
    beneficiary    = get_object_or_404(Beneficiary, pk=pk)
    saved_document = DocumentBeneficiary.objects.filter(beneficiary=beneficiary).first()

    if request.method == 'POST':
        form     = UpdateBeneficiaryForm(request.POST, instance=beneficiary)
        doc_form = DocumentBeneficiaryForm(request.POST, request.FILES, instance=saved_document)

        if form.is_valid():
            form.save()

            if request.FILES.get('file'):
                documento             = doc_form.save(commit=False)
                documento.beneficiary = beneficiary
                documento.save()

            messages.success(request, 'Beneficiario actualizado exitosamente.')

            notify_beneficiary(beneficiary.id, "Actualización de Datos - Buro Juridico ICESI", 
                               beneficiary.name + " se han actualizado sus datos en la plataforma de Buro")

            return redirect('beneficiary_list')

        messages.error(request, 'Corrige los errores del formulario')
    else:
        form     = UpdateBeneficiaryForm(instance=beneficiary)
        doc_form = DocumentBeneficiaryForm(instance=saved_document)

    return render(request, 'beneficiary/beneficiary_update.html', {
        'form':               form,
        'doc_form':           doc_form,
        'documento_existente': saved_document,
    })


@login_required
def beneficiary_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    documento   = DocumentBeneficiary.objects.filter(beneficiary=beneficiary).first()
    return render(request, 'beneficiary/beneficiary_detail.html', {
        'beneficiary': beneficiary,
        'documento':   documento,
    })


@login_required
def beneficiary_audit_log(request, beneficiary_id):
    user = request.user
    has_access = (
        user.is_staff
        or user.groups.filter(name__in=[ROLE_SECRETARIA, ROLE_ADMINISTRADOR]).exists()
    )
    if not has_access:
        messages.error(request, 'No tienes permiso para ver esta bitacora.')
        return redirect('beneficiary_list')

    beneficiary = get_object_or_404(Beneficiary, pk=beneficiary_id)
    logs = BeneficiaryAuditLog.objects.filter(
        beneficiary=beneficiary
    ).select_related('user').order_by('-timestamp')

    return render(request, 'beneficiary/beneficiary_audit_log.html', {
        'beneficiary': beneficiary,
        'logs':        logs,
        'page_title':  f'Bitacora - {beneficiary.name}',
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
        'page_title': 'Bitacora Global de Datos Personales',
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def data_deletion_request_create(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)

    if request.method == 'POST':
        form = DataDeletionRequestForm(request.POST)
        if form.is_valid():
            deletion_request             = form.save(commit=False)
            deletion_request.beneficiary = beneficiary
            deletion_request.save()

            BeneficiaryAuditLog.objects.create(
                beneficiary=beneficiary,
                user=request.user,
                action='DELETE_REQUEST',
                description=(
                    f'Se registro una solicitud de eliminacion de datos para '
                    f'{beneficiary.name}.'
                ),
                beneficiary_document='',
                beneficiary_name=beneficiary.name,
            )

            messages.success(
                request,
                'La solicitud de eliminacion de datos fue registrada correctamente.'
            )

            notify_beneficiary(beneficiary.id, "Solicitud de Eliminación de la plataforma - Buro Juridico Universidad Icesi",
                               beneficiary.name + " usted a realizado una solicitud de eliminación de sus datos personales de la "
                               "plataforma Buro Juridico de Icesi. Su solicitud sera revisada y se le informara de su estado")
            return redirect('beneficiary_detail', pk=beneficiary.pk)

        messages.error(request, 'Por favor confirma la solicitud antes de continuar.')
    else:
        form = DataDeletionRequestForm()

    return render(request, 'beneficiary/data_deletion_request_form.html', {
        'beneficiary': beneficiary,
        'form':        form,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def data_deletion_request_list(request):
    status_filter  = (request.GET.get('status') or '').strip()
    valid_statuses = {value for value, _ in DataDeletionRequest.STATUS_CHOICES}

    requests = DataDeletionRequest.objects.select_related('beneficiary')
    if status_filter in valid_statuses:
        requests = requests.filter(status=status_filter)
    else:
        status_filter = ''

    requests = requests.order_by('-request_date')

    return render(request, 'beneficiary/data_deletion_request_list.html', {
        'requests':       requests,
        'status_choices': DataDeletionRequest.STATUS_CHOICES,
        'current_status': status_filter,
    })  
