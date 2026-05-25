from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect

from cases.forms import CaseEvaluationForm
from cases.models import Case, CaseEvaluation

from .constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_PROFESOR, ROLE_SECRETARIA
from .decorators import role_required
from .forms import AcademicStudentRegistrationForm


@login_required
def no_permission(request):
    return render(request, 'accounts/no_permission.html', status=403)


def _get_student_case_history(student):
    return (
        Case.objects.filter(
            Q(assigned_student=student)
            | Q(reassignment_logs__old_student=student)
            | Q(reassignment_logs__new_student=student)
        )
        .exclude(status=Case.STATUS_DRAFT)
        .select_related('beneficiary')
        .distinct()
        .order_by('-created_at', '-pk')
    )


def _build_student_history_context(student, request_user, evaluation_form=None):
    assigned_cases = student.assigned_cases.exclude(status='borrador').order_by('-created_at')
    case_history   = _get_student_case_history(student)
    evaluations    = (
        CaseEvaluation.objects.filter(student=student)
        .select_related('case', 'professor')
        .order_by('-created_at')
    )
    can_evaluate = (
        request_user.is_superuser
        or request_user.groups.filter(name__in=[ROLE_PROFESOR, ROLE_ADMINISTRADOR]).exists()
    )
    if evaluation_form is None and can_evaluate:
        evaluation_form = CaseEvaluationForm(case_queryset=case_history)

    return {
        'student':            student,
        'assigned_cases':     assigned_cases,
        'active_cases_count': assigned_cases.count(),
        'case_history':       case_history,
        'evaluations':        evaluations,
        'evaluation_form':    evaluation_form,
        'can_evaluate':       can_evaluate,
    }


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

                profile                       = user.profile
                profile.student_code          = form.cleaned_data['student_code']
                profile.max_cases             = form.cleaned_data['max_cases']
                profile.availability          = form.cleaned_data['availability']
                profile.preferred_room        = form.cleaned_data['preferred_room']
                profile.supervising_professor = form.cleaned_data['supervising_professor']
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
    ).select_related('profile').annotate(
        active_cases_count=Count(
            'assigned_cases',
            filter=~Q(assigned_cases__status='borrador'),
            distinct=True,
        )
    ).distinct().order_by('first_name', 'last_name', 'username')

    return render(request, 'accounts/academic_student_list.html', {
        'students':        students,
        'detail_url_name': 'academic_student_detail',
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
        'student':            student,
        'assigned_cases':     assigned_cases,
        'active_cases_count': assigned_cases.count(),
    })


@role_required(ROLE_PROFESOR, ROLE_ADMINISTRADOR)
def academic_student_history_list(request):
    students = User.objects.filter(
        groups__name=ROLE_ESTUDIANTE
    ).select_related('profile').annotate(
        active_cases_count=Count(
            'assigned_cases',
            filter=~Q(assigned_cases__status='borrador'),
            distinct=True,
        )
    ).distinct().order_by('first_name', 'last_name', 'username')

    return render(request, 'accounts/academic_student_list.html', {
        'students':        students,
        'detail_url_name': 'academic_student_history',
    })


@role_required(ROLE_PROFESOR, ROLE_ADMINISTRADOR)
def academic_student_history(request, pk):
    student = get_object_or_404(
        User.objects.select_related('profile').prefetch_related('assigned_cases__beneficiary'),
        pk=pk,
        groups__name=ROLE_ESTUDIANTE,
    )
    context = _build_student_history_context(student, request.user)

    return render(request, 'accounts/academic_student_history.html', context)


@role_required(ROLE_PROFESOR, ROLE_ADMINISTRADOR)
def academic_student_add_evaluation(request, pk):
    student = get_object_or_404(
        User.objects.select_related('profile'),
        pk=pk,
        groups__name=ROLE_ESTUDIANTE,
    )

    if request.method != 'POST':
        return redirect('academic_student_history', pk=pk)

    case_history = _get_student_case_history(student)
    form         = CaseEvaluationForm(request.POST, case_queryset=case_history)

    if form.is_valid():
        evaluation           = form.save(commit=False)
        evaluation.student   = student
        evaluation.professor = request.user
        evaluation.save()
        messages.success(request, 'La retroalimentacion fue registrada correctamente.')
        return redirect('academic_student_history', pk=pk)

    context = _build_student_history_context(student, request.user, evaluation_form=form)
    messages.error(request, 'Por favor corrige los errores del formulario de retroalimentacion.')
    return render(request, 'accounts/academic_student_history.html', context)