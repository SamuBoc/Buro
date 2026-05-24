from django.urls import path

from . import views

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('panel-academico/', views.academic_dashboard, name='academic_dashboard'),
    path('panel-academico/estudiante/<int:student_id>/', views.academic_student_detail, name='case_academic_student_detail'),
    path('panel-academico/exportar/excel/', views.export_academic_dashboard_excel, name='academic_dashboard_export_excel'),
    path('panel-academico/exportar/pdf/', views.export_academic_dashboard_pdf, name='academic_dashboard_export_pdf'),
    path('registrar/', views.case_create, name='case_create'),
    path('borradores/', views.case_draft_list, name='case_draft_list'),
    path('borradores/<int:pk>/editar/', views.case_edit_draft, name='case_edit_draft'),
    path('<int:pk>/', views.case_detail, name='case_detail'),
    path('<int:pk>/fecha-limite/', views.case_update_deadline, name='case_update_deadline'),
    path('notificaciones/',                            views.notification_list,           name='notification_list'),
    path('notificaciones/<int:notification_id>/leer/', views.mark_notification_read,      name='mark_notification_read'),
    path('notificaciones/leer-todas/',                 views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notificaciones/contador/',                   views.unread_notifications_count,  name='unread_count'),
    path('<int:case_id>/bitacora/', views.case_audit_log, name='case_audit_log'),
    path('bitacora/global/',        views.global_audit_log, name='global_audit_log'),
    path('<int:pk>/reasignar/', views.case_reassign, name='case_reassign'),
    path('<int:pk>/rechazar/', views.case_reject, name='case_reject'),
    path('reportes/por-estado/', views.case_report_by_state, name='case_report_by_state'),
    path('reportes/por-sala/', views.case_report_by_sala, name='case_report_by_sala'),
    path('exportar/excel/', views.export_cases_excel, name='export_cases_excel'),
    path('exportar/pdf/', views.export_cases_pdf, name='export_cases_pdf'),
    path('documentos/<int:document_id>/ver/', views.serve_case_document, name='serve_case_document'),
    path('<int:case_id>/interacciones/', views.case_add_interaction, name='case_add_interaction'),
]
