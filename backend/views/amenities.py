import pytz
import datetime
import string
import random
import requests
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from .paytm.Checksum import *
from ..models import *

HOUR_START = 8
HOUR_END = 22
INDIA = pytz.timezone('Asia/Calcutta')


def get_new_order_id(length):
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    while (TownshipPayment.objects.filter(paytm_order_id=random_str).count() != 0) and (
            Payment.objects.filter(paytm_order_id=random_str).count() != 0):
        random_str = ''.join(random.sample(letters, length))
    return random_str


def generate_dict(amenity):
    data = dict()
    data['amenity_id'] = amenity.id
    data['name'] = amenity.name
    data['billing_rate'] = amenity.billing_rate
    data['time_period'] = amenity.time_period
    data['free_for_members'] = amenity.free_for_members
    return data


def generate_booking_dict(booking):
    data = dict()
    user = booking.user
    data['amenity_id'] = booking.amenity_id
    data['first_name'] = user.first_name
    data['last_name'] = user.last_name
    data['wing_id'] = user.wing_id
    data['apartment'] = user.apartment
    data['booking_from'] = booking.billing_from.astimezone(INDIA)
    data['booking_to'] = booking.billing_to.astimezone(INDIA)
    if booking.payment is None:
        data['payment'] = False
    else:
        data['payment'] = True
        payment = booking.payment
        data['payment_amount'] = payment.amount
        if payment.mode == 1:
            data['payment_mode'] = 'Cash'
        elif payment.mode == 2:
            data['payment_mode'] = 'Cheque'
        elif payment.mode == 3:
            data['payment_mode'] = 'PayTm'
    return data


def generate_membership_payments_dict(payment):
    data = dict()
    user = payment.user
    data['first_name'] = user.first_name
    data['last_name'] = user.last_name
    data['wing_id'] = user.wing_id
    data['apartment'] = user.apartment
    data['amount'] = payment.amount
    if payment.mode == 1:
        data['mode'] = 'Cash'
    elif payment.mode == 2:
        data['mode'] = 'Cheque'
    elif payment.mode == 3:
        data['mode'] = 'PayTm'
    return data


@csrf_exempt
def get_amenities(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    amenities = Amenity.objects.filter(township=user.township)
    return JsonResponse([{'login_status': 1, 'request_status': 1}, [generate_dict(amenity) for amenity in amenities]],
                        safe=False)


@csrf_exempt
def get_available_slots(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    amenity_id = request.POST['amenity_id']
    day = int(request.POST['day'])
    month = int(request.POST['month'])
    year = int(request.POST['year'])

    first_slot_start = INDIA.localize(datetime.datetime(year, month, day, HOUR_START))
    last_slot_end = INDIA.localize(datetime.datetime(year, month, day, HOUR_END))

    bookings = Booking.objects.filter(amenity_id=amenity_id, billing_from__gte=first_slot_start,
                                      billing_to__lte=last_slot_end).order_by('billing_from')

    slots = []
    hour = HOUR_START
    while hour < HOUR_END:
        slot = INDIA.localize(datetime.datetime(year, month, day, hour))
        slots.append(slot)
        hour += 1

    for booking in bookings:
        if booking.billing_from.astimezone(INDIA) in slots:
            slots.remove(booking.billing_from.astimezone(INDIA))

    def generate_slot_dict(s):
        data = dict()
        data['billing_from'] = s
        data['billing_to'] = INDIA.localize(datetime.datetime(s.year, s.month, s.day, s.hour + 1))
        return data

    return JsonResponse([{'login_status': 1, 'request_status': 1}, [generate_slot_dict(slot) for slot in slots]],
                        safe=False)


@csrf_exempt
def check_membership_status(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'resident':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    membership_payments = Payment.objects.filter(user=user, type=1, sub_type=2).order_by('-timestamp')
    if len(membership_payments) == 0:
        return JsonResponse([{'login_status': 1, 'request_status': 1}, {'membership_status': False}], safe=False)

    payment = membership_payments[0]
    timestamp = payment.timestamp

    if timestamp < (INDIA.localize(datetime.datetime.now()) - datetime.timedelta(days=365)):
        return JsonResponse([{'login_status': 1, 'request_status': 1}, {'membership_status': False}], safe=False)

    return JsonResponse([{'login_status': 1, 'request_status': 1}, {'membership_status': True}], safe=False)


@csrf_exempt
def book_amenity(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'resident':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    amenity_id = request.POST['amenity_id']
    day = int(request.POST['day'])
    month = int(request.POST['month'])
    year = int(request.POST['year'])
    hour = int(request.POST['hour'])

    booking = Booking.objects.create()
    booking.user = user
    booking.amenity_id = amenity_id
    booking.billing_from = INDIA.localize(datetime.datetime(year, month, day, hour))
    booking.billing_to = INDIA.localize(datetime.datetime(year, month, day, hour + 1))
    booking.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_booking_dict(booking)], safe=False)


@csrf_exempt
def get_booking_history(request):
    # will show one time bookings to the resident and admin
    # admin can filter if he wants just one time or member bookings as well
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type == 'resident':
        bookings = Booking.objects.filter(user=user).order_by('-billing_from')

    if user.type == 'admin':
        bookings = Booking.objects.filter(township=user.township).order_by('-billing_from')

    return JsonResponse(
        [{'login_status': 1, 'request_status': 1}, [generate_booking_dict(booking) for booking in bookings]],
        safe=False)


@csrf_exempt
def get_membership_payments(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    payments = Payment.objects.filter(township=user.township, type=1, sub_type=2).order_by('-timestamp')

    return JsonResponse([{'login_status': 1, 'request_status': 1},
                         [generate_membership_payments_dict(payment) for payment in payments]], safe=False)


@csrf_exempt
def membership_payment_initiate(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'resident':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    paytm_params = dict()
    paytm_params['MID'] = settings.PAYTM_MERCHANT_ID
    paytm_params['ORDER_ID'] = get_new_order_id(50)
    paytm_params['CUST_ID'] = user.paytm_cust_id
    paytm_params['TXN_AMOUNT'] = request.POST['TXN_AMOUNT']
    paytm_params['CHANNEL_ID'] = request.POST['CHANNEL_ID']
    paytm_params['WEBSITE'] = request.POST['WEBSITE']
    paytm_params['CALLBACK_URL'] = request.POST['CALLBACK_URL'] + paytm_params['ORDER_ID']
    paytm_params['INDUSTRY_TYPE_ID'] = request.POST['INDUSTRY_TYPE_ID']
    paytm_params['CHECKSUMHASH'] = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)

    payment = Payment.objects.create()
    payment.user = user
    payment.township = user.township
    payment.amount = paytm_params['TXN_AMOUNT']
    payment.timestamp = timezone.now()
    payment.mode = Payment.MODE_PAYTM
    payment.type = Payment.TYPE_CREDIT
    payment.sub_type = Payment.SUB_TYPE_MEMBERSHIP
    payment.description = request.POST.get('description', None)
    payment.paytm_order_id = paytm_params['ORDER_ID']
    payment.paytm_checksumhash = paytm_params['CHECKSUMHASH']
    payment.paytm_transaction_status = Payment.TXN_POSTED
    payment.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, paytm_params], safe=False)


@csrf_exempt
def membership_payment_verify(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'resident':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    paytm_params = {}
    paytm_params["MID"] = settings.PAYTM_MERCHANT_ID
    paytm_params["ORDERID"] = request.POST['ORDER_ID']
    paytm_params["CHECKSUMHASH"] = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
    post_data = json.dumps(paytm_params)

    # for Staging
    url = "https://securegw-stage.paytm.in/order/status"

    # for Production
    # url = "https://securegw.paytm.in/order/status"

    response = requests.post(url, data=post_data, headers={"Content-type": "application/json"}).json()
    payment = Payment.objects.get(paytm_order_id=paytm_params["ORDERID"])

    if response['STATUS'] == 'TXN_SUCCESS':
        payment.paytm_transaction_status = Payment.TXN_SUCCESSFUL
        payment.save()
        send_mail(
            f'Payment confirmation by {settings.APP_NAME}',
            f'Your payment of ₹{payment.amount} towards your township for membership is successful!',
            settings.DOMAIN_EMAIL,
            [payment.user.email],
            fail_silently=False,
        )

    return JsonResponse([response, generate_membership_payments_dict(payment)], safe=False)

