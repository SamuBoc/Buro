from django.urls import path

from . import views

urlpatterns = [
    path('beneficiario/<str:beneficiary_id>/agendar/', views.create_cite, name='create_cite'),
    path('beneficiario/<str:beneficiary_id>/', views.beneficiary_cites, name='beneficiary_cites'),
    path('beneficiario/<str:pk>/reprogramar/', views.reschedule_cite, name='reschedule_cite')
]
