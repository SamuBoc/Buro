from django.urls import path

from . import views

urlpatterns = [
    path('sin-permisos/', views.no_permission, name='no_permission'),
]
