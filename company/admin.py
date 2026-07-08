from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']

    def has_add_permission(self, request):
        # Singleton: only the one existing row may be edited, never added.
        return False
