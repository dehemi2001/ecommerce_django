from accounts.models import Account
from django.db import models
from store.models import Product, AttributeValue, ProductConfiguration
from django.db.models import Count

# Create your models here.

class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.cart_id

class CartItem(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute_values = models.ManyToManyField(AttributeValue, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    @property
    def price(self):
        avs = self.attribute_values.all()
        configs = ProductConfiguration.objects.annotate(
            av_count=Count('attribute_values', distinct=True)
        ).filter(product=self.product, is_active=True, av_count=len(avs))
        for av in avs:
            configs = configs.filter(attribute_values=av)
        config = configs.first()
        return config.price if config else self.product.price

    def sub_total(self):
        return self.price * self.quantity

    def __unicode__(self):
        return self.product