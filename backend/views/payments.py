from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from ..models import *
from .paytm.Checksum import *

import requests, json

def get_new_order_id(length):
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    while (TownshipPayment.objects.filter(paytm_order_id=random_str).count() != 0) and (Payment.objects.filter(paytm_order_id=random_str).count() != 0):
        random_str = ''.join(random.sample(letters, length))
    return random_str


@csrf_exempt
def get_checksumhash(request):
    application_id = request.POST['application_id']
    township = Township.objects.get(application_id=application_id)

    paytm_params = {}
    paytm_params['MID'] = settings.PAYTM_MERCHANT_ID
    paytm_params['ORDER_ID'] = get_new_order_id(50)
    paytm_params['CUST_ID'] = township.paytm_cust_id
    paytm_params['TXN_AMOUNT'] = request.POST['TXN_AMOUNT']
    paytm_params['CHANNEL_ID'] = request.POST['CHANNEL_ID']
    paytm_params['WEBSITE'] =  request.POST['WEBSITE']
    paytm_params['CALLBACK_URL'] = request.POST['CALLBACK_URL'] + paytm_params['ORDER_ID']
    paytm_params['INDUSTRY_TYPE_ID'] = request.POST['INDUSTRY_TYPE_ID']

    print(paytm_params)
    checksum = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
    paytm_params['CHECKSUMHASH'] = checksum

    township_payment = TownshipPayment.objects.create()
    township_payment.township = township
    township_payment.amount = paytm_params['TXN_AMOUNT']
    township_payment.timestamp = timezone.now()
    # TODO: Replace by constant defined in the class
    township_payment.mode = 3
    township_payment.paytm_order_id = paytm_order_id=paytm_params['ORDER_ID']
    # TODO: Replace by constant defined in the class
    township_payment.paytm_transaction_status = 0
    township_payment.paytm_checksumhash = checksum
    township_payment.save()

    return JsonResponse([paytm_params], safe=False)


@csrf_exempt
def verify_checksumhash(request):
    paytm_params = {}
    paytm_params["MID"] = settings.PAYTM_MERCHANT_ID
    paytm_params["ORDERID"] = request.POST['ORDER_ID']
    checksum = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
    paytm_params["CHECKSUMHASH"] = checksum
    post_data = json.dumps(paytm_params)


    # for Staging
    url = "https://securegw-stage.paytm.in/order/status"

    # for Production
    # url = "https://securegw.paytm.in/order/status"

    response = requests.post(url, data = post_data, headers = {"Content-type": "application/json"}).json()
    township_payment = TownshipPayment.objects.get(paytm_order_id=paytm_params['ORDERID'])

    if response['STATUS'] == 'TXN_SUCCESS':
        # TODO: Replace by constant defined in the class
        township_payment.paytm_transaction_status = 1

    return JsonResponse([response], safe=False)
