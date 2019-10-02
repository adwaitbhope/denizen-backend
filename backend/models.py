from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class Image(models.Model):
    # image = models.Image
    pass


class Township(models.Model):
    application_id = models.CharField(max_length=10, unique=True, default='0')
    registration_timestamp = models.DateTimeField(default=timezone.now)
    verified = models.BooleanField(default=False)
    verification_link = models.CharField(max_length=20, default=None, blank=True, null=True)
    verification_timestamp = models.DateTimeField(default=None, blank=True, null=True)

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

    paytm_cust_id = models.CharField(max_length=64, default=None, blank=True, null=True)


class Wing(models.Model):
    name = models.CharField(max_length=20)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    floors = models.IntegerField()
    apts_per_floor = models.IntegerField()

    # Specifies the naming convention for apartments in the wing
    # 1 ==> "Per apartment", eg. A/34
    # 2 ==> "Per floor", eg. A/34 will become A/902 (assuming 4 apartments per floor)
    naming_convention = models.IntegerField(default=None, blank=True, null=True)


class User(AbstractUser):
    reset_password_link = models.CharField(max_length=15, default=None, blank=True, null=True)
    reset_password_request_timestamp = models.DateTimeField(default=None, blank=True, null=True)

    phone = models.CharField(max_length=10, default=None, blank=True, null=True)
    profile_updated = models.BooleanField(default=False)

    # Type of user, values can be 'admin', 'resident' or 'security'
    type = models.CharField(max_length=10, default='resident')

    # Only applicable to type 'admin'
    designation = models.CharField(max_length=30, default=None, blank=True, null=True)

    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)

    # Only applicable to type 'resident'
    wing = models.ForeignKey(Wing, on_delete=models.CASCADE, default=None, blank=True, null=True)
    apartment = models.CharField(max_length=10, default=None, blank=True, null=True)

    paytm_cust_id = models.CharField(max_length=64, default=None, blank=True, null=True)


class Amenity(models.Model):
    name = models.CharField(max_length=20)
    township = models.ForeignKey(Township, on_delete=models.CASCADE)
    billing_rate = models.IntegerField()

    # 1 ==> "Per hour", amenity will be billed by the hour
    # 2 ==> "Per day", amenity will be billed by the day
    time_period = models.IntegerField(default=None, blank=True, null=True)

    # To specify interval of billing
    # Eg. if it is set to 2, billing will be done for every 2 hours or every 2 days (as per the time_period attribute)
    amt_time_period = models.IntegerField(default=1)

    # amount will be charged only if amenity is not free for members
    free_for_members = models.BooleanField(default=False)


class TownshipPayment(models.Model):
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    # 1 ==> "Cash"
    # 2 ==> "Cheque"
    # 3 ==> "PayTM"
    mode = models.IntegerField(default=None, blank=True, null=True)
    paytm_order_id = models.CharField(max_length=50, default=None, blank=True, null=True)
    paytm_checksumhash = models.CharField(max_length=108, default=None, blank=True, null=True)

    # 0 ==> "Posted"
    # 1 ==> "Successful"
    # 2 ==> "Failed"
    # 3 ==> "Pending"
    paytm_transaction_status = models.IntegerField(default=None, blank=True, null=True)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    # 1 ==> "Cash"
    # 2 ==> "Cheque"
    # 3 ==> "PayTM"
    mode = models.IntegerField(default=None, blank=True, null=True)

    # 1 ==> "Credit" (w.r.t. township's account)
    # 2 ==> "Debit"
    type = models.IntegerField(default=None, blank=True, null=True)

    # 1 ==> "Maintenance"
    # 2 ==> "Membership"
    # 3 ==> "Amenity"
    # 0 ==> "Other"
    sub_type = models.IntegerField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)

    cheque_no = models.CharField(max_length=6, default=None, blank=True, null=True)
    paytm_order_id = models.CharField(max_length=50, default=None, blank=True, null=True)
    paytm_checksumhash = models.CharField(max_length=108, default=None, blank=True, null=True)

    # 1 ==> "Successful"
    # 2 ==> "Failed"
    # 3 ==> "Pending"
    paytm_transaction_status = models.IntegerField(default=None, blank=True, null=True)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, default=None, blank=True, null=True)
    billing_from = models.DateTimeField(default=None, blank=True, null=True)
    billing_to = models.DateTimeField(default=None, blank=True, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, default=None, blank=True, null=True)


class Notice(models.Model):
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    wings = models.ManyToManyField(Wing)
    title = models.CharField(max_length=40, default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)


class Comment(models.Model):
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, default=None, blank=True, null=True)
    content = models.TextField(default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)



class Complaint(models.Model):
    resident = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    title = models.CharField(max_length=40, default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)


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
