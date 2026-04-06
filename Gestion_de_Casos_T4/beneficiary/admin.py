from django.contrib import admin
from .models import Beneficiary


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'phone', 'email', 'date_register')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('date_register',)
    ordering = ('-date_register',)
