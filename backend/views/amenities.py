import pytz
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
import datetime
from ..models import *

HOUR_START = 8
HOUR_END = 22
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

    def generate_booking_dict():
        data = dict()
        data['amenity_id'] = amenity_id
        data['booking_from'] = booking.billing_from.astimezone(INDIA)
        data['booking_to'] = booking.billing_to.astimezone(INDIA)
        return data

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_booking_dict()], safe=False)


@csrf_exempt
def get_booking_history(request):
    # will shoe one time bookings to the resident and admin
    # admin can filter if he wants just one time or member bookings as well
    pass


@csrf_exempt
def get_membership_payments(request):
    # will show residents who paid membership fees to the admin
    pass
