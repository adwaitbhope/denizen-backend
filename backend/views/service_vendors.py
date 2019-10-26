from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from ..models import *


def generate_dict(vendor):
    data_dict = dict()
    data_dict['vendor_id'] = vendor.id
    data_dict['first_name'] = vendor.first_name
    data_dict['last_name'] = vendor.last_name
    data_dict['phone'] = vendor.last_name
    data_dict['work'] = vendor.work
    return data_dict


@csrf_exempt
def get_service_vendors(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    vendors = ServiceVendor.objects.filter(township=user.township)
    return JsonResponse([{'login_status': 1, 'request_status': 1}, [generate_dict(vendor) for vendor in vendors]],
                        safe=False)


@csrf_exempt
def add_new_service_vendor(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    phone = request.POST['phone']
    work = request.POST['work']

    vendor = ServiceVendor.objects.create(first_name=first_name, last_name=last_name, phone=phone, work=work, township=user.township)

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_dict(vendor)], safe=False)


@csrf_exempt
def edit_service_vendor(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    vendor = ServiceVendor.objects.get(pk=request.POST['vendor_id'])
    vendor.first_name = request.POST.get('first_name', vendor.first_name)
    vendor.last_name = request.POST.get('last_name', vendor.last_name)
    vendor.phone = request.POST.get('phone', vendor.phone)
    vendor.work = request.POST.get('work', vendor.work)
    vendor.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_dict(vendor)], safe=False)


@csrf_exempt
def delete_service_vendor(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    vendor = ServiceVendor.objects.get(pk=request.POST['vendor_id'])
    vendor.delete()

    return JsonResponse([{'login_status': 1, 'request_status': 1}], safe=False)
