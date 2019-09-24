from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from itertools import chain
from fpdf import FPDF
from ..models import *
import os, random, string
from django.conf import settings


def create_pdf(township, admin_creds, security_creds, resident_creds):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(38, 10, township.name, border='B', ln=1, align='C')
    pdf.ln()

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 6, 'Admins', border=0, ln=1, align='L')

    pdf.set_font('Times', '', 10)
    for admin in admin_creds:
        pdf.set_x(20)
        pdf.cell(20, 4, 'Username: ', border=0, ln=0, align='L')
        pdf.cell(20, 4, admin['username'], border=0, ln=1, align='L')
        pdf.set_x(20)
        pdf.cell(20, 4, 'Password: ', border=0, ln=0, align='L')
        pdf.cell(20, 4, admin['password'], border=0, ln=1, align='L')
        pdf.ln()

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

    pdf.ln()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 6, 'Residents', border=0, ln=1, align='L')

    for resident in resident_creds:
        pdf.set_x(20)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(20, 4, resident['apartment'], border=0, ln=1, align='L')
        pdf.set_x(20)
        pdf.set_font('Times', '', 10)
        pdf.cell(20, 4, 'Username: ', border=0, ln=0, align='L')
        pdf.cell(20, 4, resident['username'], border=0, ln=1, align='L')
        pdf.set_x(20)
        pdf.cell(20, 4, 'Password: ', border=0, ln=0, align='L')
        pdf.cell(20, 4, resident['password'], border=0, ln=1, align='L')
        pdf.ln()

    path = township.application_id + '.pdf'
    pdf.output(path)
    return path


def create_details_pdf(township):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(14)
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(50, 10, township.name, border='0', ln=1, align='C')
    pdf.set_font('Arial', '', 14)
    pdf.cell(20, 6, 'Application ID: ' + township.application_id, border=0, ln=0, align='L')
    pdf.ln()
    pdf.ln()
    pdf.ln()

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(50, 8, 'Township details', border='', ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Name: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.cell(50, 6, township.name, border=0, ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Phone: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.cell(50, 6, township.phone, border=0, ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Address: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.set_left_margin(54)
    pdf.write(6, township.address)
    pdf.set_left_margin(14)

    pdf.ln()
    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Location: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.set_text_color(0, 0, 255)
    pdf.write(6, 'Click here', 'https://www.google.com/maps/search/?api=1&query=' + str(township.lat) + ',' + str(township.lng))
    pdf.ln()
    pdf.ln()

    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 8, 'Applicant details', border='', ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Name: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.cell(50, 6, township.applicant_name, border=0, ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Designation: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.cell(50, 6, township.applicant_designation, border=0, ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Email: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.cell(50, 6, township.applicant_email, border=0, ln=1, align='L')

    pdf.set_font('Times', 'B', 14)
    pdf.cell(40, 6, 'Phone: ', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 14)
    pdf.cell(50, 6, township.applicant_phone, border=0, ln=1, align='L')

    details_path = township.application_id + '_details.pdf'
    pdf.output(details_path)
    return details_path


def random_string(length):
    letters = string.ascii_lowercase + string.digits
    random_str = ''.join(random.sample(letters, length))
    while User.objects.filter(username=random_str).count() != 0:
        random_str = ''.join(random.sample(letters, length))
    return random_str


def get_township_verification_link(length):
    letters = string.ascii_letters + string.digits
    random_str = ''.join(random.sample(letters, length))
    while Township.objects.filter(verification_link=random_str).count() != 0:
        random_str = ''.join(random.sample(letters, length))
    return random_str


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

    data = {}
    data['username'] = user.username
    data['first_name'] = user.first_name
    data['last_name'] = user.last_name
    data['type'] = user.type
    data['phone'] = user.phone
    data['email'] = user.email
    data['profile_updated'] = user.profile_updated
    data['township'] = user.township.name

    if user.type == 'admin':
        data['designation'] = user.designation

    if user.type == 'resident':
        data['wing'] = user.wing.name
        data['apartment'] = user.apartment

    return JsonResponse([{'login': 1}, data], safe=False)


@csrf_exempt
def register_existing(request):
    application_id = request.POST['application_id']
    township = Township.objects.get(application_id=application_id)

    admin_ids = int(request.POST['admin_ids'])
    security_ids = int(request.POST['security_ids'])
    wings_num = int(request.POST['wings_num'])

    resident_credentials = []
    for i in range(wings_num):
        wing_name = request.POST['wing_' + str(i) + '_name']
        wing_floors = request.POST['wing_' + str(i) + '_floors']
        wing_apts_per_floor = request.POST['wing_' + str(i) + '_apts_per_floor']
        wing_naming_convention = request.POST['wing_' + str(i) + '_naming_convention']

        wing = Wing.objects.create(township=township, name=wing_name, floors=wing_floors, apts_per_floor=wing_apts_per_floor, naming_convention=wing_naming_convention)

        for floor in range(int(wing_floors)):
            for apt in range(int(wing_apts_per_floor)):
                random_uname = random_string(8)
                random_pwd = random_string(8)

                apartment = '0'
                if wing_naming_convention == '1':
                    apartment = str(floor * int(wing_apts_per_floor) + apt + 1)
                elif wing_naming_convention == '2':
                    apartment = str(floor + 1) + str(apt + 1).zfill(2)

                resident_credentials.append({'apartment': wing_name + '/' + apartment, 'username': random_uname, 'password': random_pwd})
                resident = User.objects.create_user(username=random_uname, password=random_pwd, township=township, type='resident', wing=wing, apartment=apartment)


    amenities_num = int(request.POST['amenities_num'])
    for i in range(amenities_num):
        amenity_name = request.POST['amenity_' + str(i) + '_name']
        amenity_billing_rate = request.POST['amenity_' + str(i) + '_rate']
        amenity_amt_time_period = request.POST.get('amenity_' + str(i) + '_amt_time_period', 1)
        amenity_time_period = request.POST['amenity_' + str(i) + '_time_period']
        amenity = Amenity.objects.create(township=township, name=amenity_name, billing_rate=amenity_billing_rate, amt_time_period=amenity_amt_time_period, time_period=amenity_time_period)

    admin_credentials = []
    for i in range(admin_ids):
        random_uname = random_string(8)
        random_pwd = random_string(8)

        admin = User.objects.create_user(username=random_uname, password=random_pwd, township=township, type='admin')
        admin_credentials.append({'username':random_uname, 'password':random_pwd})

    security_credentials = []
    for i in range(security_ids):
        random_uname = random_string(8)
        random_pwd = random_string(8)

        security = User.objects.create_user(username=random_uname, password=random_pwd, township=township, type='security')
        security_credentials.append({'username':random_uname, 'password':random_pwd})

    pdf_path = create_pdf(township, admin_credentials, security_credentials, resident_credentials)
    email = EmailMessage('Welcome to Township Manager', 'Thank you for registering with us.\nPFA the document containing login credentials for everyone.\n\nP.S. Username and password both must be changed upon first login.', 'noreply@township-manager.com', [township.applicant_email])
    email.content_subtype = 'html'
    email.attach_file(pdf_path)
    email.send()

    os.remove(pdf_path)

    return JsonResponse([{'registration_status':1}, admin_credentials, security_credentials, resident_credentials], safe=False)


@csrf_exempt
def register_new(request):
    applicant_name = request.POST['applicant_name']
    applicant_phone = request.POST['applicant_phone']
    applicant_email = request.POST['applicant_email']
    applicant_designation = request.POST['applicant_designation']

    name = request.POST['name']
    address = request.POST['address']
    phone = request.POST['phone']
    geo_address = request.POST.get('geo_address', None)
    lat = request.POST['lat']
    lng = request.POST['lng']

    file = request.FILES['certificate']

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

    verification_link = get_township_verification_link(20)

    township = Township.objects.create(application_id=application_id, applicant_name=applicant_name, applicant_phone=applicant_phone, applicant_email=applicant_email, applicant_designation=applicant_designation, name=name, address=address, phone=phone, geo_address=geo_address, lat=lat, lng=lng, verification_link=verification_link)

    certificate_path = township.application_id + '_certificate.pdf'

    dest = open(certificate_path, 'wb')
    if file.multiple_chunks:
        for c in file.chunks():
            dest.write(c)
    else:
        dest.write(file.read())
    dest.close()

    details_path = create_details_pdf(township)

    html = get_template('approve_township.html')
    html_content = html.render({'township_name': township.name, 'applicant_name' : township.applicant_name, 'verification_link' : settings.CURRENT_DOMAIN + '/register/new/verify/' + township.verification_link})

    email_subject = 'New application! (' + township.application_id + ')'
    email_to = ['adwaitbhope@gmail.com', 'vinodkamat98@gmail.com', 'atharvadhekne@gmail.com', 'aashayz28@gmail.com']
    email = EmailMultiAlternatives(email_subject, 'A new society has submitted an application', 'noreply@township-manager.com', email_to)
    email.attach_alternative(html_content, "text/html")
    email.content_subtype = 'html'
    email.attach_file(details_path)
    email.attach_file(certificate_path)
    email.send()

    os.remove(details_path)
    os.remove(certificate_path)

    client_email = EmailMessage('Thank you for registering!', 'Your application has been submitted successfully, and your Application ID is ' + township.application_id, 'noreply@township-manager.com', [township.applicant_email])
    client_email.send()

    return JsonResponse([{'registration_status' : 1, 'application_id' : application_id}], safe=False)


@csrf_exempt
def verify_township(request, verification_link):
    township = Township.objects.get(verification_link=verification_link)
    township.verified = True
    township.save()

    client_email = EmailMessage('Your application is verified', 'Your application has been verified by our administrators, you can now continute to step two and complete your registration', 'noreply@township-manager.com', [township.applicant_email])
    client_email.send()

    return HttpResponse(township.name + ' is now verified!')
