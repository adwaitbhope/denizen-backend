from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.template.loader import get_template
from pusher_push_notifications import PushNotifications
from .paytm.Checksum import *
from ..models import *
import string
import random
import requests
import json

PAGINATION_SIZE = 15


def generate_dict(payment):
    data_dict = dict()
    data_dict['payment_id'] = payment.id
    data_dict['amount'] = payment.amount
    data_dict['wing_id'] = payment.user.wing_id
    data_dict['apartment'] = payment.user.apartment
    if payment.mode == Payment.CASH:
        data_dict['mode'] = 'Cash'
    elif payment.mode == Payment.CHEQUE:
        data_dict['mode'] = 'Cheque'
        data_dict['cheque_no'] = payment.cheque_no
    else:
        data_dict['mode'] = 'PayTm'
        data_dict['paytm_order_id'] = payment.paytm_order_id
    data_dict['first_name'] = payment.user.first_name
    data_dict['last_name'] = payment.user.last_name
    data_dict['timestamp'] = payment.timestamp
    return data_dict


def get_new_order_id(length):
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    while (TownshipPayment.objects.filter(paytm_order_id=random_str).count() != 0) and (
            Payment.objects.filter(paytm_order_id=random_str).count() != 0):
        random_str = ''.join(random.sample(letters, length))
    return random_str


@csrf_exempt
def pay_maintenance_initiate(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'resident':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    paytm_params = {}
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
    payment.sub_type = Payment.MAINTENANCE
    payment.description = request.POST.get('description', None)
    payment.paytm_order_id = paytm_params['ORDER_ID']
    payment.paytm_checksumhash = paytm_params['CHECKSUMHASH']
    payment.paytm_transaction_status = Payment.TXN_POSTED
    payment.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, paytm_params], safe=False)


@csrf_exempt
def pay_maintenance_verify(request):
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
        html_content = html.render({'reason': 'Maintenance', 'amount': str(payment.amount)})

        client_email = EmailMultiAlternatives('Payment successful',
                                              f'Payment of ₹{str(payment.amount)} towards your township has been successful.',
                                              settings.DOMAIN_EMAIL, [payment.user.email])
        client_email.attach_alternative(html_content, "text/html")
        client_email.content_subtype = 'html'
        client_email.send()

    return JsonResponse([response, generate_dict(payment)], safe=False)


@csrf_exempt
def add_resident_maintenance_by_admin(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    resident = User.objects.get(wing_id=request.POST['wing_id'], apartment=request.POST['apartment'])

    payment = Payment.objects.create()
    payment.user = resident
    payment.township = resident.township
    payment.amount = request.POST['amount']
    payment.timestamp = timezone.now()
    payment.mode = int(request.POST['payment_mode'])
    payment.type = Payment.CREDIT
    payment.sub_type = Payment.MAINTENANCE
    payment.description = request.POST.get('description', None)
    if int(request.POST['payment_mode']) == Payment.CHEQUE:
        payment.cheque_no = str(request.POST['cheque_no'])
    payment.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_dict(payment)], safe=False)


@csrf_exempt
def get_maintenance_payments(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    timestamp = request.POST.get('timestamp', timezone.now())

    if user.type == 'admin':
        payments = Payment.objects.prefetch_related().filter(township=user.township,
                                                             sub_type=Payment.MAINTENANCE,
                                                             timestamp__lt=timestamp).exclude(
            paytm_transaction_status=Payment.TXN_POSTED).order_by('-timestamp')[
                   :PAGINATION_SIZE]
    else:
        payments = Payment.objects.prefetch_related().filter(township=user.township, user=user,
                                                             sub_type=Payment.MAINTENANCE,
                                                             timestamp__lt=timestamp).exclude(
            paytm_transaction_status=Payment.TXN_POSTED).order_by('-timestamp')[
                   :PAGINATION_SIZE]

    return JsonResponse([{'login_status': 1, 'request_status': 1}, [generate_dict(payment) for payment in payments]],
                        safe=False)
