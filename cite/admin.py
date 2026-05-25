from django.contrib import admin
from .models import Cite

@admin.register(Cite)
class CiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'beneficiary', 'date_assigned', 'modality_cite', 'state_cite', 'request_cite', 'description')
    search_fields = ('id', 'name', 'date_assigned')
    list_filter = ('date_assigned',)
    ordering = ('-date_assigned',)