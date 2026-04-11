from django.contrib import admin

from .models import Case, CaseDocument, CaseReassignmentLog


class CaseDocumentInline(admin.TabularInline):
    model = CaseDocument
    extra = 1
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'sala',
        'beneficiary',
        'assigned_student',
        'state',
        'created_at',
    )
    list_filter = ('sala', 'state', 'created_at')
    search_fields = (
        'code',
        'description',
        'beneficiary__name',
        'assigned_student__username',
        'assigned_student__first_name',
        'assigned_student__last_name',
    )
    autocomplete_fields = ('beneficiary', 'assigned_student')
    readonly_fields = ('code', 'created_at')
    inlines = [CaseDocumentInline]


@admin.register(CaseDocument)
class CaseDocumentAdmin(admin.ModelAdmin):
    list_display = ('case', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('case__code', 'file')
    autocomplete_fields = ('case',)
    readonly_fields = ('uploaded_at',)


@admin.register(CaseReassignmentLog)
class CaseReassignmentLogAdmin(admin.ModelAdmin):
    list_display = ('case', 'old_student', 'new_student', 'changed_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = (
        'case__code',
        'old_student__username',
        'old_student__first_name',
        'old_student__last_name',
        'new_student__username',
        'new_student__first_name',
        'new_student__last_name',
        'changed_by__username',
        'changed_by__first_name',
        'changed_by__last_name',
    )
    autocomplete_fields = ('case', 'old_student', 'new_student', 'changed_by')
    readonly_fields = ('created_at',)
