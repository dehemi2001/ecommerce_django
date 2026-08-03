from django.contrib import admin
from django.contrib import messages
from .models import Product, Attribute, AttributeValue, ReviewRating, ProductGallery, ProductConfiguration
import admin_thumbnails
from django import forms
from django.utils.safestring import mark_safe


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class AttributeValuesWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        value_ids = [str(v) for v in (value or [])]

        html = '<div class="attribute-values-widget" style="display: flex; gap: 20px; flex-wrap: wrap;">'
        for attr in Attribute.objects.all():
            html += f'<div style="flex: 1; min-width: 200px;"><label style="font-weight: 600; display: block; margin-bottom: 4px;">{attr.name}</label>'
            html += f'<select class="attr-dropdown vTextField" data-attr-id="{attr.id}" style="width: 100%; padding: 6px; border: 1px solid #ccc; border-radius: 4px;">'
            html += '<option value="">--- Select ---</option>'
            for av in attr.values.all():
                selected = 'selected' if str(av.id) in value_ids else ''
                html += f'<option value="{av.id}" {selected}>{av.value}</option>'
            html += '</select></div>'

        current_value = ','.join(value_ids)
        html += f'<input type="hidden" name="{name}" id="id_{name}" value="{current_value}" />'
        html += '</div>'

        html += '''<script>
        (function() {
            var container = document.currentScript.parentElement;
            var hidden = container.querySelector('input[type="hidden"]');
            function syncHidden() {
                var values = [];
                container.querySelectorAll('select.attr-dropdown').forEach(function(sel) {
                    if (sel.value) values.push(sel.value);
                });
                hidden.value = values.join(',');
            }
            container.querySelectorAll('select.attr-dropdown').forEach(function(sel) {
                sel.addEventListener('change', syncHidden);
            });
        })();
        </script>'''
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        raw = data.get(name, '')
        if raw:
            return [int(x) for x in raw.split(',') if x]
        return []

    def format_value(self, value):
        return value


class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = '__all__'
        widgets = {
            'attribute_values': AttributeValuesWidget(),
        }

    def clean(self):
        from django.core.exceptions import ValidationError
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        attribute_values = cleaned_data.get('attribute_values')
        
        if product and attribute_values:
            av_ids = sorted(str(av.id if hasattr(av, 'id') else av) for av in attribute_values)
            signature = '_'.join(av_ids) if av_ids else ''
            
            qs = ProductConfiguration.objects.filter(
                product=product, configuration_signature=signature
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if signature and qs.exists():
                raise ValidationError(
                    'This combination of attribute values already exists for this product.'
                )
        
        return cleaned_data


class ReviewRatingInline(admin.TabularInline):
    model = ReviewRating
    extra = 0
    readonly_fields = ('user', 'subject', 'review', 'rating', 'ip', 'status')
    can_delete = False


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'category', 'modified_date', 'is_available', 'is_deleted')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline, ReviewRatingInline]
    list_filter = ('is_available', 'is_deleted')
    readonly_fields = ('is_deleted', 'deleted_at')
    actions = ['soft_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        return Product.all_objects.all()

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f'{queryset.count()} product(s) were soft deleted.', messages.SUCCESS)
    soft_delete_selected.short_description = 'Soft delete selected products'

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f'{queryset.count()} product(s) were restored.', messages.SUCCESS)
    restore_selected.short_description = 'Restore selected products'

    def delete_model(self, request, obj):
        obj.soft_delete()
        self.message_user(request, 'Product was soft deleted.', messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f'{queryset.count()} product(s) were soft deleted.', messages.SUCCESS)


admin.site.register(Product, ProductAdmin)


class ProductConfigurationAdmin(admin.ModelAdmin):
    form = ProductConfigurationForm
    list_display = ('product_name_display', 'attributes_display', 'stock', 'price', 'is_active', 'updated_date', 'is_deleted')
    list_editable = ('stock', 'price', 'is_active')
    list_filter = ('is_active', 'product', 'is_deleted')
    search_fields = ('product__product_name',)
    list_per_page = 25
    readonly_fields = ('is_deleted', 'deleted_at')
    actions = ['soft_delete_selected', 'restore_selected']

    def get_queryset(self, request):
        return ProductConfiguration.all_objects.all()

    def product_name_display(self, obj):
        return obj.product.product_name
    product_name_display.short_description = 'Product'
    product_name_display.admin_order_field = 'product__product_name'

    def attributes_display(self, obj):
        return ', '.join(str(av) for av in obj.attribute_values.all())
    attributes_display.short_description = 'Attributes'

    def soft_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f'{queryset.count()} configuration(s) were soft deleted.', messages.SUCCESS)
    soft_delete_selected.short_description = 'Soft delete selected configurations'

    def restore_selected(self, request, queryset):
        for obj in queryset:
            obj.restore()
        self.message_user(request, f'{queryset.count()} configuration(s) were restored.', messages.SUCCESS)
    restore_selected.short_description = 'Restore selected configurations'

    def delete_model(self, request, obj):
        obj.soft_delete()
        self.message_user(request, 'Configuration was soft deleted.', messages.SUCCESS)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.soft_delete()
        self.message_user(request, f'{queryset.count()} configuration(s) were soft deleted.', messages.SUCCESS)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        obj.configuration_signature = obj._compute_signature()
        ProductConfiguration.objects.filter(pk=obj.pk).update(configuration_signature=obj.configuration_signature)


admin.site.register(ProductConfiguration, ProductConfigurationAdmin)


class AttributeValueInlineAdmin(admin.TabularInline):
    model = AttributeValue
    extra = 1


class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeValueInlineAdmin]


admin.site.register(Attribute, AttributeAdmin)
