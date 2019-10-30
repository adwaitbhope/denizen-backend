from django.http import JsonResponse
# from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.conf import settings
from pusher_push_notifications import PushNotifications
from ..models import *
import pytz
import datetime


@csrf_exempt
def get_finances(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    maintenance_payments = Payment.objects.filter(township=user.township, type=Payment.CREDIT,
                                                  sub_type=Payment.MAINTENANCE,
                                                  paytm_transaction_status=Payment.TXN_SUCCESSFUL).aggregate(
        Sum('amount'))

    return JsonResponse([{'login_status': 1, 'request_status': 1}, maintenance_payments], safe=False)


@csrf_exempt
def add_credit(request):
    pass


@csrf_exempt
def add_debit(request):
    pass
