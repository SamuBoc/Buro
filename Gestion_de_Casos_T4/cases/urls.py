from django.urls import path

from . import views

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('registrar/', views.case_create, name='case_create'),
    path('<int:pk>/', views.case_detail, name='case_detail'),
    path('<int:pk>/fecha-limite/', views.case_update_deadline, name='case_update_deadline'),
    path('notificaciones/',                            views.notification_list,           name='notification_list'),
    path('notificaciones/<int:notification_id>/leer/', views.mark_notification_read,      name='mark_notification_read'),
    path('notificaciones/leer-todas/',                 views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notificaciones/contador/',                   views.unread_notifications_count,  name='unread_count'),
    path('<int:case_id>/bitacora/', views.case_audit_log, name='case_audit_log'),
    path('bitacora/global/',        views.global_audit_log, name='global_audit_log'),
    path('<int:pk>/reasignar/', views.case_reassign, name='case_reassign'),
]
