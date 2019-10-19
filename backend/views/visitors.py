from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
# from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from pusher_push_notifications import PushNotifications
from ..models import *

@csrf_exempt
def add_visitor_entry(request):
    pass


@csrf_exempt
def get_visitor_history(request):
    pass
