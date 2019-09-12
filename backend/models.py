from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class User(AbstractUser):
    apartment = models.CharField(max_length=20)
    phone = models.CharField(max_length=10, default=None, blank=True, null=True)

    # Type of user, values can be 'admin', 'resident' or 'security'
    type = models.CharField(max_length=10, default='resident')


class Township(models.Model):
    application_id = models.CharField(max_length=10, unique=True, default='0')
    registration_timestamp = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)

    # Applicant details
    applicant_name = models.CharField(max_length=30)
    applicant_phone = models.CharField(max_length=10)
    applicant_email = models.CharField(max_length=35)
    applicant_designation = models.CharField(max_length=20)

    # Township details
    name = models.CharField(max_length=50)
    address = models.TextField()
    phone = models.CharField(max_length=10)
    geo_address = models.TextField(default=None, blank=True, null=True)
    lat = models.FloatField()
    lng = models.FloatField()


class Wing(models.Model):
    name = models.CharField(max_length=20)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    floors = models.IntegerField()
    apts_per_floor = models.IntegerField()

    # Specifies the naming convention for apartments in the wing
    # 1 ==> "Per apartment", eg. A/34
    # 2 ==> "Per floor", eg. A/34 will become A/902 (assuming 4 apartments per floor)
    naming_convention = models.IntegerField(default=None, blank=True, null=True)


class Amenity(models.Model):
    name = models.CharField(max_length=20)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    billing_rate = models.IntegerField()

    # 1 ==> "Per hour", amenity will be billed by the hour
    # 2 ==> "Per day", amenity will be billed by the day
    time_period = models.IntegerField(default=None, blank=True, null=True)

    # To specify interval of billing
    # Eg. if it is set to 2, billing will be done for every 2 hours or every 2 days (as per the time_period attribute)
    amt_time_period = models.IntegerField()

    # amount will be charged only if amenity is not free for members
    free_for_members = models.BooleanField(default=False)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, default=None, blank=True, null=True)
    billing_from = models.DateTimeField(default=None, blank=True, null=True)
    billing_to = models.DateTimeField(default=None, blank=True, null=True)
    amount = models.IntegerField(default=None, blank=True, null=True)


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
