from accounts.models import Account
from django.db import models
from category.models import Category
from django.urls import reverse
from django.db.models import Avg, Count

# Create your models here.

class Product(models.Model):
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True)
    images = models.ImageField(upload_to='photos/products')
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    @property
    def price(self):
        configs = ProductConfiguration.objects.filter(product=self, is_active=True).aggregate(min_price=models.Min('price'))
        return configs['min_price'] or 0

    @property
    def total_stock(self):
        configurations = ProductConfiguration.objects.filter(product=self, is_active=True)
        return sum(config.stock for config in configurations)

    def __str__(self):
        return self.product_name

    def averageReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = ReviewRating.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count

    # Global attribute helpers for templates
    @property
    def available_colors(self):
        """Returns distinct global color attribute values used by this product's active configurations."""
        return AttributeValue.objects.filter(
            attribute__name__iexact='color',
            productconfiguration__product=self,
            productconfiguration__is_active=True
        ).distinct()

    @property
    def available_specifications(self):
        """Returns distinct global specification attribute values used by this product's active configurations."""
        return AttributeValue.objects.filter(
            attribute__name__iexact='specification',
            productconfiguration__product=self,
            productconfiguration__is_active=True
        ).distinct()


class Attribute(models.Model):
    """Global attribute category (e.g. 'Color', 'RAM', 'Storage', 'Size')."""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class AttributeValue(models.Model):
    """Global attribute value (e.g. 'Black', '16GB', '512GB') linked to an Attribute."""
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

    class Meta:
        ordering = ['attribute__name', 'value']
        unique_together = ('attribute', 'value')


class ProductConfiguration(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='configurations')
    attribute_values = models.ManyToManyField(AttributeValue)
    stock = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.pk:
            return
        # Ensure exactly two attribute values: one color and one specification
        av_qs = self.attribute_values.all()
        if av_qs.count() != 2:
            raise ValidationError('A product configuration must have exactly one color and one specification attribute value.')
        attribute_names = set(av.attribute.name.lower() for av in av_qs)
        if attribute_names != {'color', 'specification'}:
            raise ValidationError('Attribute values must include one color and one specification.')
        # Check for duplicate configuration for the same product
        existing = ProductConfiguration.objects.filter(product=self.product, attribute_values__in=av_qs).distinct()
        for config in existing:
            if config.id != self.id:
                other_avs = set(config.attribute_values.all())
                if other_avs == set(av_qs):
                    raise ValidationError('This combination of color and specification already exists for this product.')

    def __str__(self):
        return f"{self.product.product_name} Config"


class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.subject


class ProductGallery(models.Model):
    product = models.ForeignKey(Product, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='store/products', max_length=255)

    def __str__(self):
        return self.product.product_name

    class Meta:
        verbose_name = 'productgallery'
        verbose_name_plural = 'product gallery'