from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect

from .constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_SECRETARIA
from .decorators import role_required
from .forms import AcademicStudentRegistrationForm
from .models import UserProfile


@login_required
def no_permission(request):
    return render(request, 'accounts/no_permission.html', status=403)


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def academic_student_register(request):
    if request.method == 'POST':
        form = AcademicStudentRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)

                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                )
                user.groups.add(student_group)

                profile = user.profile
                profile.student_code = form.cleaned_data['student_code']
                profile.max_cases = form.cleaned_data['max_cases']
                profile.availability = form.cleaned_data['availability']
                profile.preferred_room = form.cleaned_data['preferred_room']
                profile.save()

            messages.success(request, 'El estudiante fue registrado correctamente.')
            return redirect('academic_student_list')

        messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = AcademicStudentRegistrationForm()

    return render(request, 'accounts/academic_student_register.html', {
        'form': form,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def academic_student_list(request):
    students = User.objects.filter(
        groups__name=ROLE_ESTUDIANTE
    ).select_related('profile').distinct().order_by('first_name', 'last_name', 'username')

    return render(request, 'accounts/academic_student_list.html', {
        'students': students,
    })


@role_required(ROLE_SECRETARIA, ROLE_ADMINISTRADOR)
def academic_student_detail(request, pk):
    student = get_object_or_404(
        User.objects.select_related('profile').prefetch_related('assigned_cases__beneficiary'),
        pk=pk,
        groups__name=ROLE_ESTUDIANTE,
    )
    assigned_cases = student.assigned_cases.exclude(status='borrador').order_by('-created_at')

    return render(request, 'accounts/academic_student_detail.html', {
        'student': student,
        'assigned_cases': assigned_cases,
    })
