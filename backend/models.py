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

    audit_period_start = models.DateTimeField(default=None, blank=True, null=True)
    audit_period_end = models.DateTimeField(default=None, blank=True, null=True)

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

    phone = models.CharField(max_length=10, default='')
    profile_updated = models.BooleanField(default=False)

    # Type of user, values can be 'admin', 'resident' or 'security'
    type = models.CharField(max_length=10, default='resident')

    # Only applicable to type 'admin'
    designation = models.CharField(max_length=30, default='')

    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)

    # Only applicable to type 'resident'
    wing = models.ForeignKey(Wing, on_delete=models.CASCADE, default=None, blank=True, null=True)
    apartment = models.CharField(max_length=10, default=None, blank=True, null=True)

    paytm_cust_id = models.CharField(max_length=64, default=None, blank=True, null=True)


class Amenity(models.Model):
    name = models.CharField(max_length=20, default=None, blank=True, null=True)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    billing_rate = models.IntegerField(default=None, blank=True, null=True)

    PER_HOUR = 1        # amenity will be billed by the hour
    PER_DAY = 2         # amenity will be billed by the day
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

    CASH = 1
    CHEQUE = 2
    PAYTM = 3
    mode = models.IntegerField(default=None, blank=True, null=True)
    paytm_order_id = models.CharField(max_length=50, default=None, blank=True, null=True)
    paytm_checksumhash = models.CharField(max_length=108, default=None, blank=True, null=True)

    TXN_POSTED = 0
    TXN_SUCCESSFUL = 1
    TXN_FAILED = 2
    TXN_PENDING = 3
    paytm_transaction_status = models.IntegerField(default=None, blank=True, null=True)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    amount = models.FloatField(default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    CASH = 1
    CHEQUE = 2
    PAYTM = 3
    mode = models.IntegerField(default=None, blank=True, null=True)

    # (w.r.t. township's account)
    CREDIT = 1
    DEBIT = 2
    type = models.IntegerField(default=None, blank=True, null=True)

    MAINTENANCE = 1
    MEMBERSHIP = 2
    AMENITY = 3
    OTHER = 0
    sub_type = models.IntegerField(default=None, blank=True, null=True)
    description = models.TextField(default=None, blank=True, null=True)

    cheque_no = models.CharField(max_length=6, default=None, blank=True, null=True)
    paytm_order_id = models.CharField(max_length=50, default=None, blank=True, null=True)
    paytm_checksumhash = models.CharField(max_length=108, default=None, blank=True, null=True)

    TXN_POSTED = 0
    TXN_SUCCESSFUL = 1
    TXN_FAILED = 2
    TXN_PENDING = 3
    paytm_transaction_status = models.IntegerField(default=None, blank=True, null=True)


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, default=None, blank=True, null=True)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
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
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    first_name = models.CharField(max_length=30, default=None, blank=True, null=True)
    last_name = models.CharField(max_length=30, default=None, blank=True, null=True)
    phone = models.CharField(max_length=10, default=None, blank=True, null=True)
    work = models.CharField(max_length=30, default=None, blank=True, null=True)


class SecurityDesk(models.Model):
    name = models.CharField(max_length=30, default=None, blank=True, null=True)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)


class SecurityPersonnel(models.Model):
    first_name = models.CharField(max_length=30, default=None, blank=True, null=True)
    last_name = models.CharField(max_length=30, default=None, blank=True, null=True)
    phone = models.CharField(max_length=10, default=None, blank=True, null=True)
    shift_days = models.IntegerField(default=None, blank=True, null=True)
    shift_start = models.TimeField(default=timezone.now)
    shift_end = models.TimeField(default=timezone.now)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)


class Visitor(models.Model):
    first_name = models.CharField(max_length=25, default=None, blank=True, null=True)
    last_name = models.CharField(max_length=25, default=None, blank=True, null=True)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)
    apartment = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True, null=True)
    in_timestamp = models.DateTimeField(default=timezone.now)
    out_timestamp = models.DateTimeField(default=None, blank=True, null=True)


class VehicleEntry(models.Model):
    license_plate = models.CharField(max_length=14, default=None, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    township = models.ForeignKey(Township, on_delete=models.CASCADE, default=None, blank=True, null=True)

    IN = 0
    OUT = 1
    direction = models.IntegerField(default=None, blank=True, null=True)


class Entry(models.Model):
    pass
