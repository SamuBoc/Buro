from django.contrib.auth.models import Group, User
from django.test import TestCase

from accounts.constants import ROLE_ESTUDIANTE
from beneficiary.models import Beneficiary
from cases.models import Case, CaseAuditLog
from cases.services import auto_assign_case, select_best_student_candidate


def _make_beneficiary(name='Beneficiario HU26'):
    return Beneficiary.objects.create(
        name=name,
        location='Cali',
        phone='3001234567',
        email='beneficiario_hu26@test.com',
    )


def _make_student(
    username,
    student_code,
    *,
    available=True,
    preferred_room=None,
    max_cases=5,
):
    user = User.objects.create_user(
        username=username,
        password='testpass123',
        email=f'{username}@icesi.edu.co',
        first_name=username.capitalize(),
    )
    group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
    user.groups.add(group)

    profile = user.profile
    profile.student_code = student_code
    profile.availability = available
    profile.preferred_room = preferred_room
    profile.max_cases = max_cases
    profile.save()
    return user


def _make_case(*, sala=Case.ROOM_CIVIL, assigned_student=None, status=Case.STATUS_COMPLETE):
    return Case.objects.create(
        sala=sala,
        description='Caso de prueba HU-26',
        beneficiary=_make_beneficiary(name=f'Beneficiario {sala}'),
        assigned_student=assigned_student,
        status=status,
    )


class HU26AcademicAutoAssignmentTests(TestCase):
    def test_selects_student_with_matching_preferred_room(self):
        student_without_match = _make_student(
            'est_general',
            '20262001',
            preferred_room=Case.ROOM_PENAL,
        )
        student_with_match = _make_student(
            'est_civil',
            '20262002',
            preferred_room=Case.ROOM_CIVIL,
        )
        case = _make_case(sala=Case.ROOM_CIVIL)

        selected = select_best_student_candidate(case)

        self.assertEqual(selected, student_with_match)
        self.assertNotEqual(selected, student_without_match)

    def test_selects_student_with_lower_active_load(self):
        student_loaded = _make_student(
            'est_cargado',
            '20262003',
            preferred_room=Case.ROOM_CIVIL,
        )
        student_light = _make_student(
            'est_ligero',
            '20262004',
            preferred_room=Case.ROOM_CIVIL,
        )
        _make_case(sala=Case.ROOM_CIVIL, assigned_student=student_loaded)
        _make_case(sala=Case.ROOM_CIVIL, assigned_student=student_loaded)
        case = _make_case(sala=Case.ROOM_CIVIL)

        selected = select_best_student_candidate(case)

        self.assertEqual(selected, student_light)

    def test_ignores_unavailable_students(self):
        unavailable_student = _make_student(
            'est_no_disponible',
            '20262005',
            available=False,
            preferred_room=Case.ROOM_CIVIL,
        )
        available_student = _make_student(
            'est_disponible',
            '20262006',
            available=True,
            preferred_room=Case.ROOM_PENAL,
        )
        case = _make_case(sala=Case.ROOM_PENAL)

        selected = select_best_student_candidate(case)

        self.assertEqual(selected, available_student)
        self.assertNotEqual(selected, unavailable_student)

    def test_ignores_students_without_academic_registration(self):
        group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
        user_without_profile_code = User.objects.create_user(
            username='est_sin_codigo',
            password='testpass123',
            email='est_sin_codigo@icesi.edu.co',
        )
        user_without_profile_code.groups.add(group)
        user_without_profile_code.profile.preferred_room = Case.ROOM_CIVIL
        user_without_profile_code.profile.max_cases = 5
        user_without_profile_code.profile.availability = True
        user_without_profile_code.profile.student_code = ''
        user_without_profile_code.profile.save()

        registered_student = _make_student(
            'est_registrado',
            '20262007',
            preferred_room=Case.ROOM_CIVIL,
        )
        case = _make_case(sala=Case.ROOM_CIVIL)

        selected = select_best_student_candidate(case)

        self.assertEqual(selected, registered_student)
        self.assertNotEqual(selected, user_without_profile_code)

    def test_auto_assign_updates_case_and_active_cases(self):
        student = _make_student(
            'est_asignado',
            '20262008',
            preferred_room=Case.ROOM_CIVIL,
        )
        case = _make_case(sala=Case.ROOM_CIVIL)

        auto_assign_case(case)
        case.refresh_from_db()
        student.refresh_from_db()

        self.assertEqual(case.assigned_student, student)
        self.assertEqual(case.state, Case.STATE_ASSIGNED)
        self.assertEqual(student.profile.active_cases, 1)

    def test_auto_assign_marks_case_without_students_when_no_capacity(self):
        student = _make_student(
            'est_sin_cupo',
            '20262009',
            preferred_room=Case.ROOM_CIVIL,
            max_cases=1,
        )
        _make_case(sala=Case.ROOM_CIVIL, assigned_student=student)
        case = _make_case(sala=Case.ROOM_CIVIL)

        auto_assign_case(case)
        case.refresh_from_db()

        self.assertIsNone(case.assigned_student)
        self.assertEqual(case.state, Case.STATE_NO_STUDENTS)

    def test_auto_assign_registers_assignment_in_audit_log(self):
        student = _make_student(
            'est_bitacora',
            '20262010',
            preferred_room=Case.ROOM_CIVIL,
        )
        case = _make_case(sala=Case.ROOM_CIVIL)

        auto_assign_case(case)

        audit_log = CaseAuditLog.objects.filter(case=case, action='ASSIGNED').first()
        self.assertIsNotNone(audit_log)
        self.assertIn('Estudiante seleccionado:', audit_log.description)
        self.assertIn(case.code, audit_log.description)

    def test_auto_assign_registers_unavailability_in_audit_log(self):
        student = _make_student(
            'est_sin_disponibilidad',
            '20262011',
            available=False,
            preferred_room=Case.ROOM_CIVIL,
        )
        case = _make_case(sala=Case.ROOM_CIVIL)

        auto_assign_case(case)

        self.assertFalse(
            CaseAuditLog.objects.filter(case=case, action='ASSIGNED').exists()
        )
        audit_log = CaseAuditLog.objects.filter(case=case, action='UPDATED').first()
        self.assertIsNotNone(audit_log)
        self.assertIn('No fue posible asignar automaticamente', audit_log.description)
