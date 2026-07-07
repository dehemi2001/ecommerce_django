from django.contrib import admin
from .models import Product, Attribute, AttributeValue, ReviewRating, ProductGallery, ProductConfiguration
import admin_thumbnails
from django import forms
from django.utils.safestring import mark_safe


@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1


class AttributeValuesWidget(forms.Widget):
    """
    Custom widget that renders the M2M attribute_values field as
    one dropdown per global attribute (Color ▼, RAM ▼, etc.).
    Uses a hidden input to store the selected IDs for Django's M2M processing.
    """
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        # value comes as a list of IDs from Django
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

        # Hidden field that holds the actual M2M value (comma-separated IDs)
        current_value = ','.join(value_ids)
        html += f'<input type="hidden" name="{name}" id="id_{name}" value="{current_value}" />'
        html += '</div>'

        # JavaScript to sync dropdown selections to the hidden field
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
        """Parse the comma-separated hidden field value back into a list of IDs."""
        raw = data.get(name, '')
        if raw:
            return [int(x) for x in raw.split(',') if x]
        return []

    def format_value(self, value):
        """Return the value as-is for rendering."""
        return value


class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = '__all__'
        widgets = {
            'attribute_values': AttributeValuesWidget(),
        }


class ReviewRatingInline(admin.TabularInline):
    model = ReviewRating
    extra = 0
    readonly_fields = ('user', 'subject', 'review', 'rating', 'ip', 'status')
    can_delete = False


class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}
    inlines = [ProductGalleryInline, ReviewRatingInline]


admin.site.register(Product, ProductAdmin)


# Standalone admin for ProductConfiguration — manage all inventory in one place
class ProductConfigurationAdmin(admin.ModelAdmin):
    form = ProductConfigurationForm
    list_display = ('product_name_display', 'attributes_display', 'stock', 'price', 'is_active', 'updated_date')
    list_editable = ('stock', 'price', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('product__product_name',)
    list_per_page = 25

    def product_name_display(self, obj):
        return obj.product.product_name
    product_name_display.short_description = 'Product'
    product_name_display.admin_order_field = 'product__product_name'

    def attributes_display(self, obj):
        return ', '.join(str(av) for av in obj.attribute_values.all())
    attributes_display.short_description = 'Attributes'


admin.site.register(ProductConfiguration, ProductConfigurationAdmin)


# Register Attribute and AttributeValue as standalone models for global management
class AttributeValueInlineAdmin(admin.TabularInline):
    model = AttributeValue
    extra = 1


class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeValueInlineAdmin]


admin.site.register(Attribute, AttributeAdmin)