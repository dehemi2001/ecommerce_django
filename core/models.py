from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    pass


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if hasattr(self, 'is_available'):
            self.is_available = False
        if hasattr(self, 'is_active'):
            self.is_active = False
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        if hasattr(self, 'is_available'):
            self.is_available = True
        if hasattr(self, 'is_active'):
            self.is_active = True
        self.save()
