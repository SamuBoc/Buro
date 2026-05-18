from django.urls import path

from . import views

urlpatterns = [
    path('sin-permisos/', views.no_permission, name='no_permission'),
    path('estudiantes/registrar/', views.academic_student_register, name='academic_student_register'),
    path('estudiantes/', views.academic_student_list, name='academic_student_list'),
    path('estudiantes/<int:pk>/', views.academic_student_detail, name='academic_student_detail'),
]
