from django.urls import path

from . import views

urlpatterns = [
    path('sin-permisos/', views.no_permission, name='no_permission'),
    path('estudiantes/registrar/', views.academic_student_register, name='academic_student_register'),
    path('estudiantes/', views.academic_student_list, name='academic_student_list'),
    path('estudiantes/<int:pk>/', views.academic_student_detail, name='academic_student_detail'),
    path('estudiantes/historial/', views.academic_student_history_list, name='academic_student_history_list'),
    path('estudiantes/<int:pk>/historial/', views.academic_student_history, name='academic_student_history'),
    path('estudiantes/<int:pk>/evaluar/', views.academic_student_add_evaluation, name='academic_student_add_evaluation'),
]
