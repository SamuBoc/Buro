from .constants import (
    ROLE_ADMINISTRADOR,
    ROLE_ESTUDIANTE,
    ROLE_PROFESOR,
    ROLE_SECRETARIA,
)


def _user_roles(user):
    return set(user.groups.values_list('name', flat=True))


def has_role(user, *roles):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(_user_roles(user).intersection(roles))


def can_view_case(user, case):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    roles = _user_roles(user)

    if roles.intersection({ROLE_ADMINISTRADOR, ROLE_SECRETARIA, ROLE_PROFESOR}):
        return True

    if ROLE_ESTUDIANTE in roles and case.assigned_student_id == user.id:
        return True

    return False


def can_reassign_case(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    roles = _user_roles(user)
    return bool(roles.intersection({ROLE_ADMINISTRADOR, ROLE_SECRETARIA, ROLE_PROFESOR}))


def can_manage_case_deadline(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    roles = _user_roles(user)
    return bool(roles.intersection({ROLE_ADMINISTRADOR, ROLE_SECRETARIA, ROLE_PROFESOR}))

def can_add_interaction(user, case):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    roles = _user_roles(user)
    if roles.intersection({ROLE_ADMINISTRADOR, ROLE_SECRETARIA, ROLE_PROFESOR}):
        return True
    if ROLE_ESTUDIANTE in roles and case.assigned_student_id == user.id:
        return True
    return False