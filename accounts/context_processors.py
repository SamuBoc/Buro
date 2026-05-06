def user_roles(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'user_roles': set()}
    return {
        'user_roles': set(user.groups.values_list('name', flat=True))
    }
