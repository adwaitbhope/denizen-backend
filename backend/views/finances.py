from django.http import JsonResponse
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from django.conf import settings
from django.template.loader import get_template
from pusher_push_notifications import PushNotifications
from ..models import *
from fpdf import FPDF
import os
import pytz
import datetime


def create_pdf(township, maintenances, memberships, one_times, expenses):
    maintenances_total = 0
    memberships_total = 0
    one_times_total = 0
    expenses_total = 0
    credit_total = 0
    for maintenance in maintenances:
        maintenances_total += maintenance.amount

    for membership in memberships:
        memberships_total += membership.amount

    for one_time in one_times:
        one_times_total += one_time.amount

    credit_total = maintenances_total + memberships_total + one_times_total
    for expense in expenses:
        expenses_total += expense.amount

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(38, 10, township.name, border='B', ln=1, align='C')
    pdf.ln()

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 6, 'Credit', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 10)
    pdf.cell(40, 6, 'Total: Rs. ' + str(credit_total), border=0, ln=1, align='L')

    pdf.set_x(20)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 6, 'Maintenance', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 10)
    pdf.cell(40, 6, 'Total: Rs. ' + str(maintenances_total), border=0, ln=1, align='L')

    pdf.set_font('Times', '', 10)
    for maintenance in maintenances:
        name = maintenance.user.first_name + ' ' + maintenance.user.last_name
        apartment = ' (' + maintenance.user.wing.name + '-' + maintenance.user.apartment + ')'
        if maintenance.mode == Payment.CASH:
            mode = 'Cash'
        elif maintenance.mode == Payment.CHEQUE:
            mode = 'Cheque' + ' (no. ' + maintenance.cheque_no + ')'
        else:
            mode = 'PayTM'
        pdf.set_x(40)
        pdf.cell(60, 4, name + apartment + ': ', border=0, ln=0, align='L')
        pdf.cell(20, 4, 'Rs. ' + str(maintenance.amount), border=0, ln=0, align='L')
        pdf.cell(20, 4, 'by ' + mode, border=0, ln=1, align='L')
        pdf.ln()

    pdf.ln()
    pdf.set_x(20)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 6, 'Membership', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 10)
    pdf.cell(40, 6, 'Total: Rs. ' + str(memberships_total), border=0, ln=1, align='L')

    pdf.set_font('Times', '', 10)
    for membership in memberships:
        name = membership.user.first_name + ' ' + membership.user.last_name
        apartment = ' (' + membership.user.wing.name + '-' + membership.user.apartment + ')'
        if membership.mode == Payment.CASH:
            mode = 'Cash'
        elif membership.mode == Payment.CHEQUE:
            mode = 'Cheque' + ' (no. ' + membership.cheque_no + ')'
        else:
            mode = 'PayTM'
        pdf.set_x(40)
        pdf.cell(60, 4, name + apartment + ': ', border=0, ln=0, align='L')
        pdf.cell(20, 4, 'Rs. ' + str(membership.amount), border=0, ln=0, align='L')
        pdf.cell(20, 4, 'by ' + mode, border=0, ln=1, align='L')
        pdf.ln()

    pdf.ln()
    pdf.set_x(20)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(150, 6, 'Amenity One Time Bookings', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 10)
    pdf.cell(40, 6, 'Total: Rs. ' + str(one_times_total), border=0, ln=1, align='L')

    pdf.set_font('Times', '', 10)
    for one_time in one_times:
        name = one_time.user.first_name + ' ' + one_time.user.last_name
        apartment = ' (' + one_time.user.wing.name + '-' + one_time.user.apartment + ')'
        if one_time.mode == Payment.CASH:
            mode = 'Cash'
        elif one_time.mode == Payment.CHEQUE:
            mode = 'Cheque' + ' (no. ' + one_time.cheque_no + ')'
        else:
            mode = 'PayTM'
        pdf.set_x(40)
        pdf.cell(60, 4, name + apartment + ': ', border=0, ln=0, align='L')
        pdf.cell(20, 4, 'Rs. ' + str(one_time.amount), border=0, ln=0, align='L')
        pdf.cell(20, 4, 'by ' + mode, border=0, ln=1, align='L')
        pdf.ln()

    pdf.ln()
    pdf.ln()
    pdf.set_x(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 6, 'Debit', border=0, ln=0, align='L')
    pdf.set_font('Times', '', 10)
    pdf.cell(40, 6, 'Total: Rs. ' + str(expenses_total), border=0, ln=1, align='L')

    pdf.set_font('Times', '', 10)
    for expense in expenses:
        name = expense.description
        if expense.mode == Payment.CASH:
            mode = 'Cash'
        elif expense.mode == Payment.CHEQUE:
            mode = 'Cheque' + ' (no. ' + expense.cheque_no + ')'
        else:
            mode = 'PayTM'
        pdf.set_x(20)
        pdf.cell(60, 4, name + ': ', border=0, ln=0, align='L')
        pdf.cell(20, 4, 'Rs. ' + str(expense.amount), border=0, ln=0, align='L')
        pdf.cell(20, 4, 'by ' + mode, border=0, ln=1, align='L')
        pdf.ln()

    path = township.application_id + '.pdf'
    pdf.output(path)
    return path


@csrf_exempt
def add_finance(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    return JsonResponse([{'login_status': 1, 'request_status': 1}], safe=False)


@csrf_exempt
def generate_report(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login_status': 0}], safe=False)

    if user.type != 'admin':
        return JsonResponse([{'login_status': 1, 'authorization': 0}], safe=False)

    maintenance_payments = Payment.objects.filter(township=user.township, type=Payment.CREDIT,
                                                  sub_type=Payment.MAINTENANCE).exclude(
        paytm_transaction_status=Payment.TXN_POSTED)

    membership_payments = Payment.objects.filter(township=user.township, type=Payment.CREDIT,
                                                 sub_type=Payment.MEMBERSHIP).exclude(
        paytm_transaction_status=Payment.TXN_POSTED)

    one_time_payments = Payment.objects.filter(township=user.township, type=Payment.CREDIT,
                                               sub_type=Payment.AMENITY).exclude(
        paytm_transaction_status=Payment.TXN_POSTED)

    expenses = Payment.objects.filter(township=user.township, type=Payment.DEBIT).exclude(
        paytm_transaction_status=Payment.TXN_POSTED)

    pdf_path = create_pdf(user.township, maintenance_payments, membership_payments, one_time_payments, expenses)

    html = get_template('finance_report.html')
    html_content = html.render({})

    email_subject = 'Financial report'
    email = EmailMultiAlternatives(email_subject, 'The financial report that you requested is attached to this email.',
                                   settings.DOMAIN_EMAIL,
                                   [user.email])
    email.attach_alternative(html_content, "text/html")
    email.content_subtype = 'html'
    email.attach_file(pdf_path)
    email.send()
    os.remove(pdf_path)

    return JsonResponse([{'login_status': 1, 'authorization': 1}], safe=False)
