from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_SECRETARIA
from accounts.decorators import role_required

from .forms import BeneficiaryForm
from .models import Beneficiary


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
            form.save()
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
