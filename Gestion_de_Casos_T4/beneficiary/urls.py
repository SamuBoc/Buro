from django.urls import path
from . import views

urlpatterns = [
    path('', views.beneficiary_list, name='beneficiary_list'),
    path('beneficiario/registrar/', views.beneficiary_register, name='beneficiary_register'),
    path('beneficiario/<int:pk>/', views.beneficiary_detail, name='beneficiary_detail'),
    path('<int:beneficiary_id>/bitacora/', views.beneficiary_audit_log,        name='beneficiary_audit_log'),
    path('bitacora/global/',               views.global_beneficiary_audit_log, name='global_beneficiary_audit_log'),
]
