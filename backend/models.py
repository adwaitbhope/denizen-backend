from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    apartment = models.CharField(max_length=20)
    phone = models.CharField(max_length=10, default=None, blank=True, null=True)
    type = models.CharField(max_length=10, default='resident')
