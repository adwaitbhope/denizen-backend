from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    apartment = models.CharField(max_length=20)
    phone = models.CharField(max_length=10, default=None, blank=True, null=True)
    type = models.CharField(max_length=10, default='resident')


class Township(models.Model):
    application_id = models.CharField(max_length=10, unique=True, default='0')
    registration_timestamp = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)

    applicant_name = models.CharField(max_length=30)
    applicant_phone = models.CharField(max_length=10)
    applicant_email = models.CharField(max_length=35)
    applicant_designation = models.CharField(max_length=20)

    name = models.CharField(max_length=50)
    address = models.TextField()
    phone = models.CharField(max_length=10)
    geo_address = models.TextField()
    lat = models.FloatField()
    lng = models.FloatField()


class Wing(models.Model):
    name = models.CharField(max_length=20)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    floors = models.IntegerField()
    apt_per_floor = models.IntegerField()
    # naming


class Amenity(models.Model):
    name = models.CharField(max_length=20)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    rate = models.IntegerField()
    amt_time_period = models.IntegerField()     # per 1 hour or per 2 hour
    # time_period hour or day


class Booking(models.Model):
    pass


class Notice(models.Model):
    pass


class Comment(models.Model):
    pass


class Complaint(models.Model):
    pass


class Group(models.Model):
    pass


class ServiceVendor(models.Model):
    pass


class SecurityDesk(models.Model):
    pass


class SecurityPersonnel(models.Model):
    pass


class Visitor(models.Model):
    pass


class Entry(models.Model):
    pass


class Payment(models.Model):
    pass
