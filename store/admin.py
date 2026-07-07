from django.contrib import admin
from .models import Product, Attribute, AttributeValue, ReviewRating, ProductGallery, ProductConfiguration
import admin_thumbnails
from django import forms

# Register your models here.

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1

class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        attribute_values = cleaned_data.get('attribute_values')
        if attribute_values is None:
            return cleaned_data
        # Ensure exactly two attribute values
        if attribute_values.count() != 2:
            raise forms.ValidationError('Select exactly one color and one specification.')
        attribute_names = set(av.attribute.name.lower() for av in attribute_values)
        if attribute_names != {'color', 'specification'}:
            raise forms.ValidationError('Attribute values must include one color and one specification.')
        # Check duplicate configuration
        product = self.instance.product
        if product:
            existing = ProductConfiguration.objects.filter(product=product, attribute_values__in=attribute_values).distinct()
            for cfg in existing:
                if cfg.id != self.instance.id:
                    other_avs = set(cfg.attribute_values.all())
                    if other_avs == set(attribute_values):
                        raise forms.ValidationError('This combination already exists for this product.')
        return cleaned_data

    # This limits the attribute value choices to ONLY values belonging to the global attributes
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "attribute_values":
            kwargs["queryset"] = AttributeValue.objects.all()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

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
    list_display = ('product_name_display', 'color_display', 'specification_display', 'stock', 'price', 'is_active', 'updated_date')
    list_editable = ('stock', 'price', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('product__product_name',)
    list_per_page = 25

    def product_name_display(self, obj):
        return obj.product.product_name
    product_name_display.short_description = 'Product'
    product_name_display.admin_order_field = 'product__product_name'

    def color_display(self, obj):
        color = obj.attribute_values.filter(attribute__name__iexact='color').first()
        return color.value if color else '-'
    color_display.short_description = 'Color'

    def specification_display(self, obj):
        spec = obj.attribute_values.filter(attribute__name__iexact='specification').first()
        return spec.value if spec else '-'
    specification_display.short_description = 'Specification'

admin.site.register(ProductConfiguration, ProductConfigurationAdmin)

# Register Attribute and AttributeValue as standalone models for global management
class AttributeValueInlineAdmin(admin.TabularInline):
    model = AttributeValue
    extra = 1

class AttributeAdmin(admin.ModelAdmin):
    inlines = [AttributeValueInlineAdmin]

admin.site.register(Attribute, AttributeAdmin)