from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse

from django.conf import settings
from .paytm.Checksum import *

def random_order_id(length):
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    return random_str


def random_cust_id(length):
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    return random_str


@csrf_exempt
def get_checksumhash(request):
    paytm_params = {}
    paytm_params['MID'] = settings.PAYTM_MERCHANT_ID
    paytm_params['ORDER_ID'] = random_order_id(50)
    paytm_params['CUST_ID'] = random_cust_id(64)
    paytm_params['TXN_AMOUNT'] = request.POST['TXN_AMOUNT']
    paytm_params['CHANNEL_ID'] = request.POST['CHANNEL_ID']
    paytm_params['WEBSITE'] =  request.POST['WEBSITE']
    paytm_params['CALLBACK_URL'] = request.POST['CALLBACK_URL'] + paytm_params['ORDER_ID']
    paytm_params['INDUSTRY_TYPE_ID'] = request.POST['INDUSTRY_TYPE_ID']

    checksum = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)

    paytm_params['CHECKSUMHASH'] = checksum

    return JsonResponse([paytm_params], safe=False)


@csrf_exempt
def verify_checksumhash(request):
    received_data = request.POST        # or something equivalent
    checksum = ''
    MERCHANT_KEY = settings.PAYTM_MERCHANT_KEY

    paytm_params = {}
    for key, value in received_data.items():
    	if key == 'CHECKSUMHASH':
    		checksum = value
    	else:
    		paytm_params[key] = value

    is_valid_checksum = verify_checksum(paytm_params, MERCHANT_KEY, checksum)

    return JsonResponse([{'checksum_verified':is_valid_checksum}], safe=False)


# 1.
# vinod:
# sagla
#
# return
# order id
# merchant id
# cust id
# checksumhash
#
#
# 2.
# checksumhash verification
