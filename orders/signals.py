from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Order
from .utils import send_order_invoice_email

STATUS_SUBJECTS = {
    'Accepted': 'Your order has been accepted',
    'Completed': 'Your order has been completed',
    'Cancelled': 'Your order has been cancelled',
}


@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status == instance.status:
        return

    new_status = instance.status
    if new_status in STATUS_SUBJECTS and instance.payment:
        send_order_invoice_email(
            order=instance,
            payment=instance.payment,
            user_email=instance.email,
            mail_subject=STATUS_SUBJECTS[new_status],
        )
