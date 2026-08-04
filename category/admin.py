from django.contrib import admin
from django.contrib import messages
from .models import Category


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}
    list_display = ('category_name', 'slug', 'is_deleted')
    list_filter = ('is_deleted',)
    readonly_fields = ('is_deleted', 'deleted_at')
    actions = ['soft_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        return Category.all_objects.all()

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f'{queryset.count()} category(ies) were soft deleted.', messages.SUCCESS)
    soft_delete_selected.short_description = 'Soft delete selected categories'

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f'{queryset.count()} category(ies) were restored.', messages.SUCCESS)
    restore_selected.short_description = 'Restore selected categories'


admin.site.register(Category, CategoryAdmin)

