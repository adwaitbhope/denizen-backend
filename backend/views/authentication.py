from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.utils import timezone
from itertools import chain

from ..models import *

@csrf_exempt
def index(request):
    return HttpResponse("Hello, world. You're at the index.")


@csrf_exempt
def login(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login': 0}], safe=False)
    return JsonResponse([{'login': 1}], safe=False)


@csrf_exempt
def register_existing(request, application_id):
    township = Township.objects.filter(application_id=application_id)

    wings_num = int(request.POST['wings_num'])
    for i in range(wings_num):
        wing_name = request.POST['wing_' + str(i) + '_name']
        wing_floors = request.POST['wing_' + str(i) + '_floors']
        wing_apt_per_floor = request.POST['wing_' + str(i) + '_apt_per_floor']
        wing_naming_convention = request.POST['wing_' + str(i) + '_naming_convention']
        wing = Wing.objects.create(township=township, name=wing_name, floors=wing_floors, apt_per_floor=wing_apt_per_floor, naming_convention=wing_naming_convention)

    amenities_num = int(request.POST['amenities_num'])
    for i in range(amenities_num):
        amenity_name = request.POST['amenity_' + str(i) + '_name']
        amenity_rate = request.POST['amenity_' + str(i) + '_rate']
        amenity_amt_time_period = request.POST['amenity_' + str(i) + '_amt_time_period']
        amenity_time_period = request.POST['amenity_' + str(i) + '_time_period']
        amenity = Amenity.objects.create(township=township, name=amenity_name, rate=amenity_rate, amt_time_period=amenity_amt_time_period, time_period=amenity_time_period)

    return JsonResponse([{'registration_status':1}], safe=False)


@csrf_exempt
def register_new(request):
    applicant_name = request.POST['applicant_name']
    applicant_phone = request.POST['applicant_phone']
    applicant_email = request.POST['applicant_email']
    applicant_designation = request.POST['applicant_designation']

    name = request.POST['name']
    address = request.POST['address']
    phone = request.POST['phone']
    geo_address = request.POST['geo_address']
    lat = request.POST['lat']
    lng = request.POST['lng']

    time = str(timezone.now())
    application_id = list(chain(time[2:4].split(), time[5:7].split(), time[8:10].split()))

    filter_app_id = application_id.copy()
    filter_app_id.extend(['0', '0', '0', '0'])
    filter_app_id = int(''.join(filter_app_id))

    townships = Township.objects.filter(application_id__gte=filter_app_id).order_by('-application_id')
    if len(townships) == 0:
        application_id.extend(['0', '0', '0', '1'])
        application_id = ''.join(application_id)
    else:
        existing_app_id = townships[0].application_id
        largest = str(existing_app_id)[-4:]
        id = str(int(largest) + 1).zfill(4).split()
        application_id.extend(id)
        application_id = ''.join(application_id)

    township = Township.objects.create(application_id=application_id, applicant_name=applicant_name, applicant_phone=applicant_phone, applicant_email=applicant_email, applicant_designation=applicant_designation, name=name, address=address, phone=phone, geo_address=geo_address, lat=lat, lng=lng)

    return JsonResponse([{'registration_status' : 1}], safe=False)
