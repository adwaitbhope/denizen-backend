from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
# from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from pusher_push_notifications import PushNotifications
from ..models import *
import pytz
import datetime

PAGINATION_SIZE = 30
INDIA = pytz.timezone('Asia/Calcutta')


@csrf_exempt
def add_visitor_entry(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'security':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    wing_id = request.POST['wing_id']
    apartment = request.POST['apartment']

    wing = Wing.objects.get(pk=int(wing_id))
    visitor_apartment = User.objects.get(wing=wing, apartment=apartment, township=user.township)

    visitor = Visitor.objects.create(first_name=first_name, last_name=last_name, apartment=visitor_apartment,
                           township=user.township, in_timestamp=timezone.now())

    beams_client = PushNotifications(instance_id=settings.BEAMS_INSTANCE_ID, secret_key=settings.BEAMS_SECRET_KEY)

    response = beams_client.publish_to_users(
        user_ids=[visitor_apartment.username],
        publish_body={
            'fcm': {
                'notification': {
                    'title': 'New visitor!',
                    'body': first_name + ' ' + last_name + ' is here to meet you',
                },
            },
        },
    )

    return JsonResponse([{'login_status': 1, 'request_status': 1, 'visitor_id': visitor.id}, {'visitor_id': visitor.id}], safe=False)


@csrf_exempt
def get_visitor_history(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    timestamp = request.POST.get('timestamp', timezone.now())

    if user.type == 'resident':
        visitors = Visitor.objects.prefetch_related().filter(township=user.township, in_timestamp__lt=timestamp,
                                                             apartment=user).order_by('-in_timestamp')[:PAGINATION_SIZE]

    else:
        visitors = Visitor.objects.prefetch_related().filter(township=user.township,
                                                             in_timestamp__lt=timestamp).order_by('-in_timestamp')[
                   :PAGINATION_SIZE]

    def generate_dict(visitor):
        data_dict = dict()
        data_dict['first_name'] = visitor.first_name
        data_dict['last_name'] = visitor.last_name
        data_dict['in_timestamp'] = str(visitor.in_timestamp.astimezone(INDIA))
        if visitor.out_timestamp is not None:
            data_dict['out_timestamp'] = str(visitor.out_timestamp.astimezone(INDIA))
        if user.type != 'resident':
            data_dict['wing'] = visitor.apartment.wing_id
            data_dict['apartment'] = visitor.apartment.apartment
        return data_dict

    return JsonResponse([{'login_status': 1, 'request_status': 1}, [generate_dict(visitor) for visitor in visitors]],
                        safe=False)


@csrf_exempt
def add_vehicle_entry(request):
    license_plate = request.POST['license_plate'].upper()
    direction = request.POST['direction']
    township_id = request.POST['township_id']

    VehicleEntry.objects.create(license_plate=license_plate, timestamp=timezone.now(), direction=direction, township_id=township_id)
    return JsonResponse({'request_status': 1})


@csrf_exempt
def get_vehicle_history(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    vehicles = VehicleEntry.objects.order_by('-timestamp')

    def generate_dict(vehicle):
        data_dict = dict()
        data_dict['license_plate'] = vehicle.license_plate
        data_dict['timestamp'] = vehicle.timestamp.astimezone(INDIA)
        data_dict['direction'] = 'IN' if vehicle.direction == VehicleEntry.IN else 'OUT'
        return data_dict

    return JsonResponse([{'login_status': 1, 'request_status': 1}, [generate_dict(vehicle) for vehicle in vehicles]],
                        safe=False)
