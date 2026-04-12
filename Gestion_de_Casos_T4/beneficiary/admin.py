from django.contrib import admin
from .models import Beneficiary


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'phone', 'email', 'date_register')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('date_register',)
    ordering = ('-date_register',)

from .models import BeneficiaryAuditLog

@admin.register(BeneficiaryAuditLog)
class BeneficiaryAuditLogAdmin(admin.ModelAdmin):
    list_display    = ['timestamp', 'beneficiary_name', 'beneficiary_document', 'action', 'user']
    list_filter     = ['action', 'timestamp']
    search_fields   = ['beneficiary_name', 'beneficiary_document', 'user__username']
    readonly_fields = [
        'beneficiary', 'user', 'action', 'description', 'timestamp',
        'changed_fields', 'beneficiary_document', 'beneficiary_name', 'ip_address',
    ]
    ordering = ['-timestamp']

    def has_add_permission(self, request):              return False
    def has_delete_permission(self, request, obj=None): return False
