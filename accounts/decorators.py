from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.groups.filter(name__in=roles).exists():
                return view_func(request, *args, **kwargs)
            return redirect('no_permission')
        return wrapper
    return decorator
