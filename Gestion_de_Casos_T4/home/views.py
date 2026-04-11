from django.shortcuts import render


def home(request):
    """Muestra la pagina principal con los accesos al sistema."""
    return render(request, 'home/home.html')
