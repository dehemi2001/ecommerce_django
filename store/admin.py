from django.contrib import admin
from .models import Product, Variation, ReviewRating, ProductGallery, ProductConfiguration
import admin_thumbnails

# Register your models here.

@admin_thumbnails.thumbnail('image')
class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1

class VariationInline(admin.TabularInline):
    model = Variation
    extra = 1

class ProductConfigurationInline(admin.TabularInline):
    model = ProductConfiguration
    extra = 1
    # This limits the variation choices to ONLY variations belonging to the current product
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "variations":
            product_id = request.resolver_match.kwargs.get('object_id')
            if product_id:
                kwargs["queryset"] = Variation.objects.filter(product_id=product_id)
            else:
                kwargs["queryset"] = Variation.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

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