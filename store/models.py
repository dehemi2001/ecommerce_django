from accounts.models import Account
from django.db import models
from category.models import Category
from django.urls import reverse
from django.db.models import Avg, Count
from decimal import Decimal

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

    @property
    def attribute_groups(self):
        """
        Returns a dict of {attribute_name: [attribute_values]} for active configurations.
        Used by the product detail template to render dropdowns dynamically.
        """
        attrs = Attribute.objects.filter(
            values__productconfiguration__product=self,
            values__productconfiguration__is_active=True
        ).distinct()
        groups = {}
        for attr in attrs:
            groups[attr.name] = attr.values.filter(
                productconfiguration__product=self,
                productconfiguration__is_active=True
            ).distinct()
        return groups

    # Backward-compatible aliases for templates that may still reference these
    @property
    def available_colors(self):
        return self.attribute_groups.get('Color', [])

    @property
    def available_specifications(self):
        return self.attribute_groups.get('Specification', [])


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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    configuration_signature = models.CharField(max_length=255, editable=False, blank=True, db_index=True)

    def _compute_signature(self):
        av_ids = sorted(str(av.id) for av in self.attribute_values.all())
        return '_'.join(av_ids) if av_ids else ''

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.pk:
            return
        av_qs = self.attribute_values.all()
        attribute_ids = set(av.attribute_id for av in av_qs)
        if len(attribute_ids) != av_qs.count():
            raise ValidationError('Each attribute can only have one value per configuration.')
        av_ids = sorted(str(av.id) for av in av_qs)
        signature = '_'.join(av_ids) if av_ids else ''
        existing = ProductConfiguration.objects.filter(product=self.product, configuration_signature=signature).exclude(pk=self.pk)
        if signature and existing.exists():
            raise ValidationError('This combination of attribute values already exists for this product.')

    def save(self, *args, **kwargs):
        if self.pk:
            self.configuration_signature = self._compute_signature()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"ProductConfiguration (product_id={self.product_id})"

    class Meta:
        unique_together = (('product', 'configuration_signature'),)


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