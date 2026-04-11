from django.contrib import admin

from .models import Case, CaseDocument


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
