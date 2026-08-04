import os

from django.conf import settings
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from category.models import Category
from company.models import Company
from store.models import Product, ProductGallery
from accounts.models import UserProfile


def _get_media_path(field_value):
    if field_value and hasattr(field_value, 'name') and field_value.name:
        return os.path.join(settings.MEDIA_ROOT, field_value.name)
    return None


def _delete_file(path):
    if path and os.path.isfile(path):
        os.remove(path)


@receiver(pre_save, sender=Category)
def category_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Category.objects.get(pk=instance.pk)
            instance._old_cat_image = old.cat_image
        except Category.DoesNotExist:
            pass


@receiver(post_save, sender=Category)
def category_post_save(sender, instance, **kwargs):
    old = getattr(instance, '_old_cat_image', None)
    new = instance.cat_image
    if old and old != new:
        _delete_file(_get_media_path(old))


@receiver(post_delete, sender=Category)
def category_post_delete(sender, instance, **kwargs):
    _delete_file(_get_media_path(instance.cat_image))


@receiver(pre_save, sender=Product)
def product_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Product.objects.get(pk=instance.pk)
            instance._old_images = old.images
        except Product.DoesNotExist:
            pass


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, **kwargs):
    old = getattr(instance, '_old_images', None)
    new = instance.images
    if old and old != new:
        _delete_file(_get_media_path(old))


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    _delete_file(_get_media_path(instance.images))


@receiver(pre_save, sender=ProductGallery)
def product_gallery_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = ProductGallery.objects.get(pk=instance.pk)
            instance._old_image = old.image
        except ProductGallery.DoesNotExist:
            pass


@receiver(post_save, sender=ProductGallery)
def product_gallery_post_save(sender, instance, **kwargs):
    old = getattr(instance, '_old_image', None)
    new = instance.image
    if old and old != new:
        _delete_file(_get_media_path(old))


@receiver(post_delete, sender=ProductGallery)
def product_gallery_post_delete(sender, instance, **kwargs):
    _delete_file(_get_media_path(instance.image))


@receiver(pre_save, sender=Company)
def company_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Company.objects.get(pk=instance.pk)
            instance._old_logo = old.logo
            instance._old_cover_image = old.cover_image
        except Company.DoesNotExist:
            pass


@receiver(post_save, sender=Company)
def company_post_save(sender, instance, **kwargs):
    old_logo = getattr(instance, '_old_logo', None)
    new_logo = instance.logo
    if old_logo and old_logo != new_logo:
        _delete_file(_get_media_path(old_logo))

    old_cover = getattr(instance, '_old_cover_image', None)
    new_cover = instance.cover_image
    if old_cover and old_cover != new_cover:
        _delete_file(_get_media_path(old_cover))


@receiver(post_delete, sender=Company)
def company_post_delete(sender, instance, **kwargs):
    _delete_file(_get_media_path(instance.logo))
    _delete_file(_get_media_path(instance.cover_image))


@receiver(pre_save, sender=UserProfile)
def userprofile_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = UserProfile.objects.get(pk=instance.pk)
            instance._old_profile_picture = old.profile_picture
        except UserProfile.DoesNotExist:
            pass


@receiver(post_save, sender=UserProfile)
def userprofile_post_save(sender, instance, **kwargs):
    old = getattr(instance, '_old_profile_picture', None)
    new = instance.profile_picture
    if old and old != new:
        _delete_file(_get_media_path(old))


@receiver(post_delete, sender=UserProfile)
def userprofile_post_delete(sender, instance, **kwargs):
    _delete_file(_get_media_path(instance.profile_picture))