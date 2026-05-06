from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def no_permission(request):
    return render(request, 'accounts/no_permission.html', status=403)
