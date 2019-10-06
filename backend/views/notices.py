from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from ..models import *

PAGINATION_SIZE = 15

@csrf_exempt
def get_notices(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    timestamp = request.POST.get('timestamp', timezone.now())

    if user.type == 'admin':
        notices = Notice.objects.prefetch_related().filter(township=user.township, timestamp__lt=timestamp).order_by('-timestamp')[:PAGINATION_SIZE]
    else:
        notices = Notice.objects.prefetch_related().filter(wings=user.wing, timestamp__lt=timestamp).order_by('-timestamp')[:PAGINATION_SIZE]

    def generate_comment_dict(comment):
        data_dict = {}
        data_dict['comment_id'] = comment.id
        data_dict['posted_by_user_id'] = comment.posted_by_id
        data_dict['posted_by_first_name'] = comment.posted_by.first_name
        data_dict['posted_by_last_name'] = comment.posted_by.last_name
        data_dict['posted_by_wing'] = comment.posted_by.wing.name
        data_dict['posted_by_apartment'] = comment.posted_by.apartment
        data_dict['content'] = comment.content
        data_dict['timestamp'] = comment.timestamp
        return data_dict

    def generate_dict(notice):
        data_dict = {}
        wings = notice.wings.all()
        comments = Comment.objects.prefetch_related().filter(notice=notice).order_by('-timestamp')
        data_dict['notice_id'] = notice.id
        data_dict['posted_by_first_name'] = notice.posted_by.first_name
        data_dict['posted_by_last_name'] = notice.posted_by.last_name
        data_dict['posted_by_designation'] = notice.posted_by.designation
        data_dict['timestamp'] = notice.timestamp
        data_dict['title'] = notice.title
        data_dict['description'] = notice.description
        data_dict['wings'] = [{'wing_id': wing.id, 'wing_name': wing.name} for wing in wings]
        data_dict['comments'] = [generate_comment_dict(comment) for comment in comments]
        return data_dict

    data = [generate_dict(notice) for notice in notices]

    return JsonResponse([{'login_status': 1, 'request_status': 1}, data], safe=False)


@csrf_exempt
def add_notice(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    title = request.POST['title']
    description = request.POST['description']
    num_wings = request.POST['num_wings']
    notice = Notice.objects.create(title=title, description=description, timestamp=timezone.now(), posted_by=user, township=user.township)

    for i in range(int(num_wings)):
        wing = Wing.objects.get(pk=request.POST['wing_' + str(i) + '_id'])
        notice.wings.add(wing)

    return JsonResponse([{'login_status': 1, 'request_status': 1}, {'notice_id': notice.id}], safe=False)


@csrf_exempt
def add_comment_on_notice(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    content = request.POST['content']
    notice_id = request.POST['notice_id']
    notice = Notice.objects.get(pk=notice_id)

    comment = Comment.objects.create(posted_by=user, content=content, notice=notice, timestamp=timezone.now())
    return JsonResponse([{'login_status': 1, 'request_status': 1}], safe=False)
