from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils import timezone
from itertools import chain
from fpdf import FPDF
from pusher_push_notifications import PushNotifications
from django.conf import settings
from .paytm.Checksum import *
from ..models import *
import os, random, string, requests, json


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


def get_new_paytm_cust_id():
    length = 64
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    while (Township.objects.filter(paytm_cust_id=random_str).count() != 0) and (User.objects.filter(paytm_cust_id=random_str).count() != 0):
        random_str = ''.join(random.sample(letters, length))
    return random_str


def get_new_order_id(length):
    letters = string.ascii_letters + string.digits + '@' + '-' + '_' + '.'
    random_str = ''.join([random.choice(letters) for _ in range(length)])
    while (TownshipPayment.objects.filter(paytm_order_id=random_str).count() != 0) and (Payment.objects.filter(paytm_order_id=random_str).count() != 0):
        random_str = ''.join(random.sample(letters, length))
    return random_str


def get_township_verification_link(length):
    letters = string.ascii_letters + string.digits
    random_str = ''.join(random.sample(letters, length))
    while Township.objects.filter(verification_link=random_str).count() != 0:
        random_str = ''.join(random.sample(letters, length))
    return random_str


def get_password_reset_link(length):
    letters = string.ascii_letters + string.digits
    random_str = ''.join(random.sample(letters, length))
    while User.objects.filter(reset_password_link=random_str).count() != 0:
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
    data['township_id'] = user.township_id

    if user.type == 'admin':
        data['designation'] = user.designation

    if user.type == 'resident':
        data['wing'] = user.wing.name
        data['wing_id'] = user.wing_id
        data['apartment'] = user.apartment

    wings = Wing.objects.filter(township=user.township)
    wings_data = [{'wing_id': wing.id, 'wing_name': wing.name} for wing in wings]

    return JsonResponse([{'login': 1}, data, wings_data], safe=False)


@csrf_exempt
def get_beams_token(request):
    username = request.headers['Username']
    password = request.headers['Password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    beams_client = PushNotifications(instance_id='f464fd4f-7e2f-4f42-91cf-8a8ef1a67acb', secret_key='5DDA12A32501E7C8A20EA4297716D189E3AFAF54601C62F417B48BA6882DA951')
    beams_token = beams_client.generate_token(username)
    return JsonResponse(beams_token, safe=False)


@csrf_exempt
def register_existing_initiate(request):
    application_id = request.POST['application_id']
    township = Township.objects.get(application_id=application_id)

    if not township.verified:
        return JsonResponse([{'request_status': 0, 'request_description': 'Township is not yet verified'}], safe=False)

    admin_ids = int(request.POST['admin_ids'])
    security_ids = int(request.POST['security_ids'])
    wings_num = int(request.POST['wings_num'])

    resident_credentials = []
    users = []
    for i in range(wings_num):
        wing_name = request.GET['wing_' + str(i) + '_name']
        wing_floors = request.GET['wing_' + str(i) + '_floors']
        wing_apts_per_floor = request.GET['wing_' + str(i) + '_apts_per_floor']
        wing_naming_convention = request.GET['wing_' + str(i) + '_naming_convention']

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
                users.append(User(username=random_uname, password=make_password(random_pwd, None, 'md5'), township=township, type='resident', wing=wing, apartment=apartment))

    amenities_num = int(request.POST['amenities_num'])
    amenities = []
    for i in range(amenities_num):
        amenity_name = request.GET['amenity_' + str(i) + '_name']
        amenity_billing_rate = request.GET['amenity_' + str(i) + '_rate']
        amenity_amt_time_period = request.GET.get('amenity_' + str(i) + '_amt_time_period', 1)
        amenity_time_period = request.GET['amenity_' + str(i) + '_time_period']
        print(request.GET['amenity_' + str(i) + '_free_for_members'])
        amenity_free_for_members = True if request.GET['amenity_' + str(i) + '_free_for_members'] == 'true' else False
        amenities.append(Amenity(township=township, name=amenity_name, billing_rate=amenity_billing_rate, amt_time_period=amenity_amt_time_period, time_period=amenity_time_period))

    admin_credentials = []
    for i in range(admin_ids):
        random_uname = random_string(8)
        random_pwd = random_string(8)
        admin_credentials.append({'username':random_uname, 'password':random_pwd})
        users.append(User(username=random_uname, password=make_password(random_pwd, None, 'md5'), township=township, type='admin'))

    security_credentials = []
    for i in range(security_ids):
        random_uname = random_string(8)
        random_pwd = random_string(8)
        security_credentials.append({'username':random_uname, 'password':random_pwd})
        users.append(User(username=random_uname, password=make_password(random_pwd, None, 'md5'), township=township, type='security'))

    User.objects.bulk_create(users)
    Amenity.objects.bulk_create(amenities)

    create_pdf(township, admin_credentials, security_credentials, resident_credentials)

    paytm_params = {}
    paytm_params['MID'] = settings.PAYTM_MERCHANT_ID
    paytm_params['ORDER_ID'] = get_new_order_id(50)
    paytm_params['CUST_ID'] = township.paytm_cust_id
    paytm_params['TXN_AMOUNT'] = request.POST['TXN_AMOUNT']
    paytm_params['CHANNEL_ID'] = request.POST['CHANNEL_ID']
    paytm_params['WEBSITE'] =  request.POST['WEBSITE']
    paytm_params['CALLBACK_URL'] = request.POST['CALLBACK_URL'] + paytm_params['ORDER_ID']
    paytm_params['INDUSTRY_TYPE_ID'] = request.POST['INDUSTRY_TYPE_ID']

    print(paytm_params)
    checksum = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
    paytm_params['CHECKSUMHASH'] = checksum

    township_payment = TownshipPayment.objects.create()
    township_payment.township = township
    township_payment.amount = paytm_params['TXN_AMOUNT']
    township_payment.timestamp = timezone.now()
    # TODO: Replace by constant defined in the class
    township_payment.mode = 3
    township_payment.paytm_order_id = paytm_order_id=paytm_params['ORDER_ID']
    # TODO: Replace by constant defined in the class
    township_payment.paytm_transaction_status = 0
    township_payment.paytm_checksumhash = checksum
    township_payment.save()

    return JsonResponse([{'request_status':1}, paytm_params], safe=False)


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
    paytm_cust_id = get_new_paytm_cust_id()

    township = Township.objects.create(application_id=application_id, applicant_name=applicant_name, applicant_phone=applicant_phone, applicant_email=applicant_email, applicant_designation=applicant_designation, name=name, address=address, phone=phone, geo_address=geo_address, lat=lat, lng=lng, verification_link=verification_link, paytm_cust_id=paytm_cust_id)

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
    html_content = html.render({'township_name': township.name, 'applicant_name' : township.applicant_name, 'verification_link' : settings.CURRENT_DOMAIN + '/register/verify/' + township.verification_link})

    email_subject = 'New application! (' + township.application_id + ')'
    email = EmailMultiAlternatives(email_subject, 'A new society has submitted an application', settings.DOMAIN_EMAIL, settings.ADMIN_EMAIL_IDS)
    email.attach_alternative(html_content, "text/html")
    email.content_subtype = 'html'
    email.attach_file(details_path)
    email.attach_file(certificate_path)
    email.send()

    os.remove(details_path)
    os.remove(certificate_path)

    client_email = EmailMessage('Thank you for registering!', 'Your application has been submitted successfully, and your Application ID is ' + township.application_id, settings.DOMAIN_EMAIL, [township.applicant_email])
    client_email.send()

    return JsonResponse([{'registration_status' : 1, 'application_id' : application_id}], safe=False)


@csrf_exempt
def register_existing_verify(request):
    application_id = request.POST['application_id']
    township = Township.objects.get(application_id=application_id)
    paytm_params = {}
    paytm_params["MID"] = settings.PAYTM_MERCHANT_ID
    paytm_params["ORDERID"] = request.POST['ORDER_ID']
    checksum = generate_checksum(paytm_params, settings.PAYTM_MERCHANT_KEY)
    paytm_params["CHECKSUMHASH"] = checksum
    post_data = json.dumps(paytm_params)

    # for Staging
    url = "https://securegw-stage.paytm.in/order/status"

    # for Production
    # url = "https://securegw.paytm.in/order/status"

    response = requests.post(url, data = post_data, headers = {"Content-type": "application/json"}).json()
    township_payment = TownshipPayment.objects.get(paytm_order_id=paytm_params['ORDERID'])

    if response['STATUS'] == 'TXN_SUCCESS':
        # TODO: Replace by constant defined in the class
        township_payment.paytm_transaction_status = 1
        township_payment.save()
        pdf_path = application_id + '.pdf'
        email = EmailMessage('Welcome to Township Manager', 'Thank you for registering with us.\nPFA the document containing login credentials for everyone.\n\nP.S. Username and password both must be changed upon first login.', settings.DOMAIN_EMAIL, [township.applicant_email])
        email.content_subtype = 'html'
        email.attach_file(pdf_path)
        email.send()
        os.remove(pdf_path)

    return JsonResponse([response], safe=False)


@csrf_exempt
def verify_township(request, verification_link):
    township = Township.objects.get(verification_link=verification_link)
    township.verified = True
    township.verification_timestamp = timezone.now()
    township.save()

    client_email = EmailMessage('Your application is verified', 'Your application has been verified by our administrators, you can now continute to step two and complete your registration', 'noreply@township-manager.com', [township.applicant_email])
    client_email.send()

    return HttpResponse(township.name + ' is now verified!')


@csrf_exempt
def check_verification(request):
    application_id = request.GET.get('application_id', None)
    email = request.GET.get('email', None)
    try:
        township = Township.objects.get(application_id=application_id, applicant_email=email)
    except Township.DoesNotExist:
        return JsonResponse([{'request_status': 0, 'status_description': 'Incorrect Application ID and Email combination'}], safe=False)

    data = {}
    data['name'] = township.name
    data['phone'] = township.phone
    data['address'] = township.address
    data['verified'] = township.verified

    return JsonResponse([{'request_status': 1}, data], safe=False)


@csrf_exempt
def send_reset_password_link(request):
    email = request.POST['email']
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return JsonResponse([{'user_found':0}], safe=False)

    reset_password_link = get_password_reset_link(15)
    user.reset_password_link = reset_password_link
    user.reset_password_request_timestamp = timezone.now()
    user.save()

    html = get_template('reset_password.html')
    html_content = html.render({'reset_password_link': reset_password_link})

    subject = 'Reset password'
    client_email = EmailMultiAlternatives('Reset password', 'To reset your password, click on the following link: ', settings.DOMAIN_EMAIL, [email])
    client_email.attach_alternative(html_content, "text/html")
    client_email.content_subtype = 'html'
    client_email.send()
    return JsonResponse([{'user_found':1, 'email_sent':1}], safe=False)


@csrf_exempt
def reset_password(request, reset_password_id):
    pass
