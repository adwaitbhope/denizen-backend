from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from ..models import *


def generate_dict(user):
    data_dict = dict()
    data_dict['user_id'] = user.id
    data_dict['type'] = user.type
    data_dict['first_name'] = user.first_name
    data_dict['last_name'] = user.last_name
    data_dict['phone'] = user.phone
    if user.type == 'resident':
        data_dict['wing_id'] = user.wing_id
        data_dict['apartment'] = user.apartment
    return data_dict


@csrf_exempt
def get_users(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    admins = User.objects.filter(township=user.township, type='admin')
    security_desks = User.objects.filter(township=user.township, type='security')
    residents = User.objects.filter(township=user.township, type='resident')

    admins_list = [generate_dict(admin) for admin in admins]
    security_list = [generate_dict(security_desk) for security_desk in security_desks]
    residents_list = [generate_dict(resident) for resident in residents]

    return JsonResponse([{'login_status': 1, 'request_status': 1}, admins_list, security_list, residents_list],
                        safe=False)
