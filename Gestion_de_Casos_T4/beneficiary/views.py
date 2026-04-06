from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Beneficiary
from .forms import BeneficiaryForm


def beneficiary_list(request):
    """Lista todos los beneficiarios registrados."""
    beneficiaries = Beneficiary.objects.all()
    return render(request, 'beneficiary/beneficiary_list.html', {
        'beneficiaries': beneficiaries
    })


def beneficiary_register(request):
    """Registra un nuevo beneficiario."""
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


def beneficiary_detail(request, pk):
    """Muestra el detalle de un beneficiario."""
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    return render(request, 'beneficiary/beneficiary_detail.html', {
        'beneficiary': beneficiary
    })
