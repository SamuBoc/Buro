from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from beneficiary.models import Beneficiary

from .forms import CiteForm
from .models import Cite


@login_required
def create_cite(request, beneficiary_id):
	beneficiary = get_object_or_404(Beneficiary, pk=beneficiary_id)

	if request.method == 'POST':
		form = CiteForm(request.POST)
		if form.is_valid():
			cite = form.save(commit=False)
			cite.beneficiary = beneficiary
			cite.save()
			messages.success(request, 'Cita agendada correctamente con la modalidad seleccionada.')
			return redirect('beneficiary_detail', pk=beneficiary.id)
		messages.error(request, 'Debes seleccionar una modalidad valida para continuar.')
	else:
		form = CiteForm()

	return render(request, 'cite/cite_form.html', {
		'form': form,
		'beneficiary': beneficiary,
	})


@login_required
def beneficiary_cites(request, beneficiary_id):
	beneficiary = get_object_or_404(Beneficiary, pk=beneficiary_id)
	cites = Cite.objects.filter(beneficiary=beneficiary).order_by('-id')

	return render(request, 'cite/cite_list.html', {
		'beneficiary': beneficiary,
		'cites': cites,
	})
