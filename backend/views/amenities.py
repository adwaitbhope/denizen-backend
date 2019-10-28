import pytz
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import datetime
from ..models import *

INDIA = pytz.timezone('Asia/Calcutta')


def generate_dict(amenity):
    data = dict()
    data['amenity_id'] = amenity.id
    data['name'] = amenity.name
    data['billing_rate'] = amenity.billing_rate
    data['time_period'] = amenity.time_period
    data['free_for_members'] = amenity.free_for_members
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

    first_slot_start = datetime.datetime(year, month, day, 8, tzinfo=pytz.UTC).astimezone(INDIA)
    last_slot_end = datetime.datetime(year, month, day, 22, tzinfo=pytz.UTC).astimezone(INDIA)

    bookings = Booking.objects.filter(amenity_id=amenity_id, billing_from__gte=first_slot_start,
                                      billing_to__lte=last_slot_end).order_by('billing_from')

    slots = []
    hour = 8
    while hour < 22:
        slot = datetime.datetime(year, month, day, hour, tzinfo=pytz.UTC).astimezone(INDIA)
        slots.append(slot)
        hour += 1

    for booking in bookings:
        if booking.billing_from.astimezone(INDIA) in slots:
            slots.remove(booking.billing_from.astimezone(INDIA))

    return JsonResponse([{'login_status': 1}], safe=False)


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
    return JsonResponse([{'login_status': 0}], safe=False)


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
    billing_from = request.POST['billing_from']
    billing_to = request.POST['billing_to']
    return JsonResponse([{'login_status': 0}], safe=False)


@csrf_exempt
def get_booking_history(request):
    # will shoe one time bookings to the resident and admin
    # admin can filter if he wants just one time or member bookings as well
    pass


@csrf_exempt
def get_membership_payments(request):
    # will show residents who paid membership fees to the admin
    pass
