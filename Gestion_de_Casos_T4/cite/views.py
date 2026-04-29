from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from beneficiary.models import Beneficiary
from beneficiary.signals import log_beneficiary_cite_attendance

from .forms import CiteForm, Reschedule_Cite
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

	return render(request, 'schedule/cite_form.html', {
		'form': form,
		'beneficiary': beneficiary,
	})


@login_required
def beneficiary_cites(request, beneficiary_id):
	beneficiary = get_object_or_404(Beneficiary, pk=beneficiary_id)
	cites = Cite.objects.filter(beneficiary=beneficiary).order_by('-id')

	return render(request, 'schedule/cite_list.html', {
		'beneficiary': beneficiary,
		'cites': cites,
	})

@login_required
def reschedule_cite(request, pk):
	cite = get_object_or_404(Cite, pk=pk)

	if request.method == 'POST':
		form = Reschedule_Cite(request.POST, instance=cite)

		if form.is_valid():
			form.save()
			return redirect('beneficiary_cites', beneficiary_id = cite.beneficiary_id)
		else:
			print(form.errors)
			messages.error(request, 'Corrige los errores del formulario')
	
	else: form = Reschedule_Cite(instance=cite)
	return render(request, 'reschedule/reschedule_cite.html', {
		'form': form,
		'cite': cite
	})

@login_required
def cancel_cite(request, pk):
	if request.method == 'POST':
		cite = get_object_or_404(Cite, pk=pk)
		cite.state_cite = Cite.STATE_CANCELED
		cite.save()
		return redirect('beneficiary_cites', beneficiary_id = cite.beneficiary_id)


@login_required
def register_cite_attendance(request, pk, status):
	cite = get_object_or_404(Cite, pk=pk)

	if request.method != 'POST':
		return redirect('beneficiary_cites', beneficiary_id=cite.beneficiary_id)

	if cite.state_cite == Cite.STATE_CANCELED:
		messages.error(request, 'No puedes registrar asistencia en una cita cancelada.')
		return redirect('beneficiary_cites', beneficiary_id=cite.beneficiary_id)

	status_map = {
		'asistio': (Cite.STATE_ATTENDED, True),
		'no-asistio': (Cite.STATE_NO_SHOW, False),
	}

	if status not in status_map:
		messages.error(request, 'Estado de asistencia no válido.')
		return redirect('beneficiary_cites', beneficiary_id=cite.beneficiary_id)

	new_state, attended = status_map[status]

	if cite.state_cite != new_state:
		cite.state_cite = new_state
		cite.save()
		log_beneficiary_cite_attendance(
			cite.beneficiary,
			cite,
			request.user,
			attended,
			ip=_get_client_ip(request),
		)
		messages.success(request, 'Asistencia registrada correctamente.')
	else:
		messages.info(request, 'La cita ya tiene este estado registrado.')

	return redirect('beneficiary_cites', beneficiary_id=cite.beneficiary_id)


def _get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		return x_forwarded_for.split(',')[0].strip()
	return request.META.get('REMOTE_ADDR')