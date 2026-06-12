from accounts.models import Account
from django.db import models
from store.models import Product, Variation, ProductConfiguration
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
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    @property
    def price(self):
        variations = self.variations.all()
        configs = ProductConfiguration.objects.filter(product=self.product, is_active=True).annotate(v_count=Count('variations', distinct=True)).filter(v_count=len(variations))
        for var in variations:
            configs = configs.filter(variations=var)
        config = configs.first()
        return config.price if config else self.product.price

    def sub_total(self):
        return self.price * self.quantity

    def __unicode__(self):
        return self.product