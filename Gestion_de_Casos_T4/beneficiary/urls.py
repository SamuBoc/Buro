from django.urls import path
from . import views

urlpatterns = [
    path('', views.beneficiary_list, name='beneficiary_list'),
    path('beneficiario/registrar/', views.beneficiary_register, name='beneficiary_register'),
    path('beneficiario/<int:pk>/', views.beneficiary_detail, name='beneficiary_detail'),
]
