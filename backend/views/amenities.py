import pytz
import datetime
import string
import random
import requests
import json
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.template.loader import get_template
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
    data['booking_id'] = booking.id
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
        if payment.mode == Payment.CASH:
            data['payment_mode'] = 'Cash'
        elif payment.mode == Payment.CHEQUE:
            data['payment_mode'] = 'Cheque'
        elif payment.mode == Payment.PAYTM:
            data['payment_mode'] = 'PayTm'
    return data


def generate_membership_payments_dict(payment):
    data = dict()
    user = payment.user
    data['payment_id'] = payment.id
    data['first_name'] = user.first_name
    data['last_name'] = user.last_name
    data['wing_id'] = user.wing_id
    data['apartment'] = user.apartment
    data['timestamp'] = payment.timestamp.astimezone(INDIA)
    data['valid_thru_timestamp'] = (payment.timestamp + datetime.timedelta(days=365)).astimezone(INDIA)
    data['amount'] = payment.amount
    if payment.mode == Payment.CASH:
        data['mode'] = 'Cash'
    elif payment.mode == Payment.CHEQUE:
        data['mode'] = 'Cheque'
    elif payment.mode == Payment.PAYTM:
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
    amenity = Amenity.objects.get(pk=amenity_id)
    day = int(request.POST['day'])
    month = int(request.POST['month'])
    year = int(request.POST['year'])

    slots = []

    if amenity.time_period == Amenity.PER_HOUR:
        first_slot_start = INDIA.localize(datetime.datetime(year, month, day, HOUR_START))
        last_slot_end = INDIA.localize(datetime.datetime(year, month, day, HOUR_END))

        bookings = Booking.objects.filter(amenity_id=amenity_id, billing_from__gte=first_slot_start,
                                          billing_to__lte=last_slot_end).order_by('billing_from')
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

        slot_dicts = [generate_slot_dict(slot) for slot in slots]

    else:
        first_slot_start = INDIA.localize(datetime.datetime(year, month, day))
        last_slot_end = INDIA.localize(datetime.datetime(year, month, day) + datetime.timedelta(days=1))
        bookings = Booking.objects.filter(amenity_id=amenity_id, billing_from__gte=first_slot_start,
                                          billing_to__lte=last_slot_end).count()
        if bookings == 0:
            slot = INDIA.localize(datetime.datetime(year, month, day, HOUR_START))
            slots.append(slot)

        def generate_slot_dict(s):
            data = dict()
            data['billing_from'] = s
            data['billing_to'] = INDIA.localize(datetime.datetime(s.year, s.month, s.day, HOUR_END))
            return data

        slot_dicts = [generate_slot_dict(slot) for slot in slots]

    return JsonResponse([{'login_status': 1, 'request_status': 1}, slot_dicts], safe=False)


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

    valid_thru_timestamp = INDIA.localize(datetime.datetime.now()) + datetime.timedelta(days=365)

    return JsonResponse([{'login_status': 1, 'request_status': 1},
                         {'membership_status': True, 'valid_thru_timestamp': valid_thru_timestamp}], safe=False)


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
    amenity = Amenity.objects.get(pk=amenity_id)
    day = int(request.POST['day'])
    month = int(request.POST['month'])
    year = int(request.POST['year'])

    booking = Booking.objects.create()
    booking.user = user
    booking.amenity_id = amenity_id
    booking.township_id = user.township_id

    if amenity.time_period == Amenity.PER_HOUR:
        hour = int(request.POST['hour'])
        booking.billing_from = INDIA.localize(datetime.datetime(year, month, day, hour))
        booking.billing_to = INDIA.localize(datetime.datetime(year, month, day, hour + 1))
    else:
        booking.billing_from = INDIA.localize(datetime.datetime(year, month, day, HOUR_START))
        booking.billing_to = INDIA.localize(datetime.datetime(year, month, day, HOUR_END))
    booking.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_booking_dict(booking)], safe=False)


@csrf_exempt
def get_booking_history(request):
    # will show one time bookings to the resident and admin
    # admin can filter if he wants just one time or member bookings as well
    username = request.POST['username']
    password = request.POST['password']
    with_payments_only = True if request.POST['with_payments_only'] == 'true' else False

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type == 'resident':
        bookings = Booking.objects.filter(user=user).order_by('-billing_from')

    if user.type == 'admin':
        if with_payments_only:
            bookings = Booking.objects.filter(township=user.township, payment=with_payments_only).order_by(
                '-billing_from')
        else:
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

    if user.type == 'admin':
        payments = Payment.objects.filter(township=user.township, type=Payment.CREDIT,
                                          sub_type=Payment.MEMBERSHIP,
                                          paytm_transaction_status=Payment.TXN_SUCCESSFUL).order_by('-timestamp')

    else:
        payments = Payment.objects.filter(user=user, type=Payment.CREDIT, sub_type=Payment.MEMBERSHIP,
                                          paytm_transaction_status=Payment.TXN_SUCCESSFUL).order_by(
            '-timestamp')

    return JsonResponse([{'login_status': 1, 'request_status': 1},
                         [generate_membership_payments_dict(payment) for payment in payments]], safe=False)


@csrf_exempt
def book_amenity_payment_initiate(request):
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
    payment.mode = Payment.PAYTM
    payment.type = Payment.CREDIT
    payment.sub_type = Payment.AMENITY
    payment.description = request.POST.get('description', None)
    payment.paytm_order_id = paytm_params['ORDER_ID']
    payment.paytm_checksumhash = paytm_params['CHECKSUMHASH']
    payment.paytm_transaction_status = Payment.TXN_POSTED
    payment.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, paytm_params], safe=False)


@csrf_exempt
def book_amenity_payment_verify(request):
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

        amenity_id = request.POST['amenity_id']
        amenity = Amenity.objects.get(pk=amenity_id)
        day = int(request.POST['day'])
        month = int(request.POST['month'])
        year = int(request.POST['year'])

        booking = Booking.objects.create()
        booking.user = user
        booking.amenity_id = amenity_id
        booking.payment = payment

        if amenity.time_period == Amenity.PER_HOUR:
            hour = int(request.POST['hour'])
            booking.billing_from = INDIA.localize(datetime.datetime(year, month, day, hour))
            booking.billing_to = INDIA.localize(datetime.datetime(year, month, day, hour + 1))
        else:
            booking.billing_from = INDIA.localize(datetime.datetime(year, month, day, HOUR_START))
            booking.billing_to = INDIA.localize(datetime.datetime(year, month, day, HOUR_END))
        booking.save()

        html = get_template('payment_successful.html')
        html_content = html.render({'reason': amenity.name + ' slot', 'amount': str(payment.amount)})

        client_email = EmailMultiAlternatives('Payment successful',
                                              f'Payment of ₹{str(payment.amount)} towards your township has been successful.',
                                              settings.DOMAIN_EMAIL, [payment.user.email])
        client_email.attach_alternative(html_content, "text/html")
        client_email.content_subtype = 'html'
        client_email.send()

    return JsonResponse([response, generate_booking_dict(booking)], safe=False)


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
    payment.mode = Payment.PAYTM
    payment.type = Payment.CREDIT
    payment.sub_type = Payment.MEMBERSHIP
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
        html = get_template('payment_successful.html')
        html_content = html.render({'reason': 'Membership', 'amount': str(payment.amount)})

        client_email = EmailMultiAlternatives('Payment successful',
                                              f'Payment of ₹{str(payment.amount)} towards your township has been successful.',
                                              settings.DOMAIN_EMAIL, [payment.user.email])
        client_email.attach_alternative(html_content, "text/html")
        client_email.content_subtype = 'html'
        client_email.send()

    return JsonResponse([response, generate_membership_payments_dict(payment)], safe=False)
