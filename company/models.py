from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='company/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='company/', blank=True, null=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    open_hours = models.CharField(max_length=200, blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    about_us = models.TextField(blank=True)
    terms_conditions = models.TextField(blank=True)
    privacy_policy = models.TextField(blank=True)

    def __str__(self):
        return self.name
