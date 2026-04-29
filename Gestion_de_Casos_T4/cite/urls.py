from django.urls import path

from . import views

urlpatterns = [
    path('beneficiario/<str:beneficiary_id>/agendar/', views.create_cite, name='create_cite'),
    path('beneficiario/<str:beneficiary_id>/', views.beneficiary_cites, name='beneficiary_cites'),
    path('beneficiario/<str:pk>/reprogramar/', views.reschedule_cite, name='reschedule_cite'),
    path('beneficiario/<int:pk>/cancelar', views.cancel_cite, name='cancel_cite'),
    path('beneficiario/<int:pk>/asistencia/<str:status>/', views.register_cite_attendance, name='register_cite_attendance')
]
