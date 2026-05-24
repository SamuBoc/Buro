from django.urls import path
from . import views

urlpatterns = [
    path('', views.beneficiary_list, name='beneficiary_list'),
    path('beneficiario/registrar/', views.beneficiary_register, name='beneficiary_register'),
    path('beneficiario/<str:pk>/', views.beneficiary_detail, name='beneficiary_detail'),
    path('beneficiario/<str:pk>/solicitar-eliminacion/', views.data_deletion_request_create, name='data_deletion_request_create'),
    path('<str:beneficiary_id>/bitacora/', views.beneficiary_audit_log, name='beneficiary_audit_log'),
    path('bitacora/global/', views.global_beneficiary_audit_log, name='global_beneficiary_audit_log'),
    path('solicitudes-eliminacion/', views.data_deletion_request_list, name='data_deletion_request_list'),
    path('beneficiario/<str:pk>/editar', views.beneficiary_update, name='beneficiary_update'),
]
