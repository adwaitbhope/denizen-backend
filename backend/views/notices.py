from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ..models import *


PAGINATION_SIZE = 15


def authenticate_wrapper(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)
    return user


@csrf_exempt
def get_notices(request):
    user = authenticate_wrapper(request)
    timestamp = request.POST.get('timestamp', timezone.now())

    if user.type == 'admin':
        notices = Notice.objects.prefetch_related().filter(township=user.township, timestamp__lt=timestamp).order_by('-timestamp')[:PAGINATION_SIZE]
    else:
        notices = Notice.objects.prefetch_related().filter(wings=user.wing, timestamp__lt=timestamp).order_by('-timestamp')[:PAGINATION_SIZE]

    def generate_dict(notice):
        data_dict = {}
        data_dict['notice_id'] = notice.id
        data_dict['posted_by_first_name'] = notice.posted_by.first_name
        data_dict['posted_by_last_name'] = notice.posted_by.last_name
        data_dict['posted_by_designation'] = notice.posted_by.designation
        data_dict['timestamp'] = notice.timestamp
        data_dict['title'] = notice.title
        data_dict['description'] = notice.description
        if user.type == 'admin':
            wings = notice.wings.all()
            data_dict['wings'] = [wing.name for wing in wings]
        return data_dict

    data = [generate_dict(notice) for notice in notices]

    return JsonResponse([{'login_status': 1, 'request_status': 1}, data], safe=False)


@csrf_exempt
def add_notice(request):
    user = authenticate_wrapper(request)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    title = request.POST['title']
    description = request.POST['description']
    num_wings = request.POST['num_wings']
    notice = Notice.objects.create(title=title, description=description, timestamp=timezone.now(), posted_by=user, township=user.township)

    for i in range(int(num_wings)):
        wing = Wing.objects.get(pk=request.POST['wing_' + str(i) + '_id'])
        notice.wings.add(wing)

    return JsonResponse([{'login_status': 1, 'request_status': 1}], safe=False)
