from django.urls import path

from . import views

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('registrar/', views.case_create, name='case_create'),
    path('<int:pk>/', views.case_detail, name='case_detail'),
    path('<int:case_id>/bitacora/', views.case_audit_log, name='case_audit_log'),
    path('bitacora/global/',        views.global_audit_log, name='global_audit_log'),
]
