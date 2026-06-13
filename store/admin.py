from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, ProductConfiguration
import admin_thumbnails
from django import forms

# Register your models here.

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1

class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        variations = cleaned_data.get('variations')
        if variations is None:
            return cleaned_data
        # Ensure exactly two variations
        if variations.count() != 2:
            raise forms.ValidationError('Select exactly one color and one specification.')
        categories = set(v.variation_category for v in variations)
        if categories != {'color', 'specification'}:
            raise forms.ValidationError('Variations must include one color and one specification.')
        # Check duplicate configuration
        product = self.instance.product
        if product:
            existing = ProductConfiguration.objects.filter(product=product, variations__in=variations).distinct()
            for cfg in existing:
                if cfg.id != self.instance.id:
                    other_vars = set(cfg.variations.all())
                    if other_vars == set(variations):
                        raise forms.ValidationError('This combination already exists for this product.')
        return cleaned_data

    # This limits the variation choices to ONLY variations belonging to the current product
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "variations":
            product_id = request.resolver_match.kwargs.get('object_id')
            if product_id:
                kwargs["queryset"] = Variation.objects.filter(product_id=product_id)
            else:
                kwargs["queryset"] = Variation.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class ProductConfigurationInline(admin.TabularInline):
    model = ProductConfiguration
    form = ProductConfigurationForm
    extra = 1

class ReviewRatingInline(admin.TabularInline):
    model = ReviewRating
    extra = 0
    readonly_fields = ('user', 'subject', 'review', 'rating', 'ip', 'status')
    can_delete = False

class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'price', 'category', 'modified_date', 'is_available')
    prepopulated_fields = {'slug': ('product_name',)}

    def get_inlines(self, request, obj=None):
        # Base inlines available during product creation
        inlines = [ProductGalleryInline, VariationInline, ReviewRatingInline]
        # Only show Configuration (Stock) if variations have been saved to the database
        if obj and Variation.objects.filter(product=obj).exists():
            inlines.insert(2, ProductConfigurationInline)
        return inlines

admin.site.register(Product, ProductAdmin)
# These are now managed inside the Product page, so we unregister them from the main menu
# admin.site.register(Variation, VariationAdmin)
# admin.site.register(ProductConfiguration, ProductConfigurationAdmin)
# admin.site.register(ReviewRating)
# admin.site.register(ProductGallery)