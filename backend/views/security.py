from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from django.conf import settings
from ..models import *
from fpdf import FPDF
import string
import os
import datetime
import random


def create_pdf(township, security_creds):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(38, 10, township.name, border='B', ln=1, align='C')
    pdf.ln()

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 6, 'Security', border=0, ln=1, align='L')

    pdf.set_font('Times', '', 10)
    for security in security_creds:
        pdf.set_x(20)
        pdf.cell(20, 4, 'Username: ', border=0, ln=0, align='L')
        pdf.cell(20, 4, security['username'], border=0, ln=1, align='L')
        pdf.set_x(20)
        pdf.cell(20, 4, 'Password: ', border=0, ln=0, align='L')
        pdf.cell(20, 4, security['password'], border=0, ln=1, align='L')
        pdf.ln()

    path = township.application_id + '.pdf'
    pdf.output(path)
    return path


def random_string(length):
    letters = string.ascii_lowercase + string.digits
    random_str = ''.join(random.sample(letters, length))
    while User.objects.filter(username=random_str).count() != 0:
        random_str = ''.join(random.sample(letters, length))
    return random_str


def generate_desk_dict(desk):
    data_dict = dict()
    data_dict['desk_id'] = desk.id
    data_dict['phone'] = desk.phone
    data_dict['designation'] = desk.designation
    return data_dict


def generate_personnel_dict(personnel):
    data_dict = dict()
    data_dict['personnel_id'] = personnel.id
    data_dict['first_name'] = personnel.first_name
    data_dict['last_name'] = personnel.last_name
    data_dict['phone'] = personnel.phone
    data_dict['shift_days'] = personnel.shift_days
    data_dict['shift_start'] = personnel.shift_start
    data_dict['shift_end'] = personnel.shift_end
    return data_dict


@csrf_exempt
def get_security_desks(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    security_desks = User.objects.filter(township=user.township, type='security')
    return JsonResponse([{'login_status': 1, 'request_status': 1},
                         [generate_desk_dict(security_desk) for security_desk in security_desks]], safe=False)


@csrf_exempt
def add_security_desk(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    security_creds = []

    random_uname = random_string(8)
    random_pwd = random_string(8)

    security_creds.append({'username': random_uname, 'password': random_pwd})
    security_desk = User.objects.create(username=random_uname, password=make_password(random_pwd, None, 'md5'),
                                        township=user.township, type='security',
                                        designation=request.POST['name'], phone=request.POST['phone'])

    pdf_path = create_pdf(user.township, security_creds)

    email = EmailMessage(f'{settings.APP_NAME} - Security credentials',
                         f"PFA the document that contains login credentials for the "
                         f"security desk that you requested.",
                         settings.DOMAIN_EMAIL, [user.email])
    email.content_subtype = 'html'
    email.attach_file(pdf_path)
    email.send()
    os.remove(pdf_path)

    return JsonResponse(
        [{'login_status': 1, 'request_status': 1}, generate_desk_dict(security_desk)],
        safe=False)


@csrf_exempt
def get_security_personnel(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    security_personnel = SecurityPersonnel.objects.filter(township=user.township)
    return JsonResponse([{'login_status': 1, 'request_status': 1},
                         [generate_personnel_dict(security) for security in security_personnel]], safe=False)


@csrf_exempt
def add_security_personnel(request):
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
    shift_start_hour = int(request.POST['shift_start_hour'])
    shift_start_minute = int(request.POST['shift_start_minute'])
    shift_end_hour = int(request.POST['shift_end_hour'])
    shift_end_minute = int(request.POST['shift_end_minute'])

    personnel = SecurityPersonnel.objects.create()
    personnel.township = user.township
    personnel.first_name = first_name
    personnel.last_name = last_name
    personnel.phone = phone
    personnel.shift_start = datetime.time(shift_start_hour, shift_start_minute)
    personnel.shift_end = datetime.time(shift_end_hour, shift_end_minute)
    personnel.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_personnel_dict(personnel)], safe=False)


@csrf_exempt
def edit_security_personnel(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    personnel = SecurityPersonnel.objects.get(pk=request.POST['personnel_id'])

    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    phone = request.POST['phone']
    shift_start_hour = int(request.POST['shift_start_hour'])
    shift_start_minute = int(request.POST['shift_start_minute'])
    shift_end_hour = int(request.POST['shift_end_hour'])
    shift_end_minute = int(request.POST['shift_end_minute'])

    personnel.first_name = first_name
    personnel.last_name = last_name
    personnel.phone = phone
    personnel.shift_start = datetime.time(shift_start_hour, shift_start_minute)
    personnel.shift_end = datetime.time(shift_end_hour, shift_end_minute)
    personnel.save()

    return JsonResponse([{'login_status': 1, 'request_status': 1}, generate_personnel_dict(personnel)], safe=False)


@csrf_exempt
def delete_security_personnel(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'request_status': 0}], safe=False)

    personnel = SecurityPersonnel.objects.get(pk=request.POST['personnel_id'])
    personnel.delete()

    return JsonResponse([{'login_status': 1, 'request_status': 1}], safe=False)