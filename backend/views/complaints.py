from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from pusher_push_notifications import PushNotifications
from ..models import *

PAGINATION_SIZE = 15

@csrf_exempt
def add_complaint(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    title = request.POST['title']
    description = request.POST['description']
    # num_photos = request.POST['num_photos']

    complaint = Complaint.objects.create(resident=user, township=user.township, title=title, description=description, timestamp=timezone.now(), resolved=False)

    beams_client = PushNotifications(instance_id=settings.BEAMS_INSTANCE_ID, secret_key=settings.BEAMS_SECRET_KEY)

    response = beams_client.publish_to_interests(
      interests=[str(user.township_id) + '-admins'],
      publish_body={
        'fcm': {
          'notification': {
            'title': 'New complaint!',
            'body': user.first_name + ': ' + title,
          },
        },
      },
    )

    return JsonResponse([{'login_status': 1, 'request_status': 1}, {'complaint_id': complaint.id}], safe = False)


@csrf_exempt
def get_complaints(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    timestamp = request.POST.get('timestamp', timezone.now())

    if user.type == 'admin':
        complaints = Complaint.objects.prefetch_related().filter(township=user.township, timestamp__lt=timestamp).order_by('-timestamp')[:PAGINATION_SIZE]
    else:
        complaints = Complaint.objects.prefetch_related().filter(resident=user, timestamp__lt=timestamp).order_by('-timestamp')[:PAGINATION_SIZE]

    def generate_dict(complaint):
        data_dict = {}
        data_dict['complaint_id'] = complaint.id
        data_dict['resident_first_name'] = complaint.resident.first_name
        data_dict['resident_last_name'] = complaint.resident.last_name
        data_dict['resident_wing'] = complaint.resident.wing.name
        data_dict['resident_apartment'] = complaint.resident.apartment
        data_dict['title'] = complaint.title
        data_dict['description'] = complaint.description
        data_dict['resolved'] = complaint.resolved
        data_dict['timestamp'] = complaint.timestamp
        return data_dict

    data = [generate_dict(complaint) for complaint in complaints]

    return JsonResponse([{'login_status': 1, 'request_status': 1}, data], safe=False)


@csrf_exempt
def mark_complaint_resolved(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    complaint_id = request.POST['complaint_id']
    complaint = Complaint.objects.get(pk=complaint_id)
    complaint.resolved = True
    complaint.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}], safe=False)
