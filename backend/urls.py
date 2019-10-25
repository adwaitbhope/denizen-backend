from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('beams/get_token/', views.get_beams_token, name='get_beams_token'),

    path('register/new/', views.register_new, name='register_new'),
    path('register/verify/<str:verification_link>/', views.verify_township, name='verify_township'),
    path('register/check_verification/', views.check_verification, name='check_verification'),

    path('register/existing/initiate/', views.register_existing_initiate, name='register_existing'),
    path('register/existing/verify/', views.register_existing_verify, name='verify_payment'),

    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/check_username_availability/', views.is_username_available, name='is_username_available'),

    path('reset_password/', views.send_reset_password_link, name='send_reset_password_link'),
    path('reset_password/<str: reset_password_id>', views.reset_password, name='reset_password'),

    path('complaints/', views.get_complaints, name='get_complaints'),
    path('complaints/new/', views.add_complaint, name='add_complaint'),
    path('complaints/resolve/', views.mark_complaint_resolved, name='resolve_complaint'),

    path('notices/', views.get_notices, name='get_notices'),
    path('notices/new/', views.add_notice, name='add_notice'),
    path('notices/comments/new/', views.add_comment_on_notice, name='add_comment_on_notice'),

    path('visitors/new/', views.add_visitor_entry, name='add_visitor'),
    path('visitors/get/', views.get_visitor_history, name='get_visitor_history'),

    path('maintenance/', views.get_maintenance_payments, name='get_maintenance_payments'),
    path('maintenance/pay/initiate/', views.pay_maintenance_initiate, name='pay_maintenance_initiate'),
    path('maintenance/pay/verify/', views.pay_maintenance_verify, name='pay_maintenance_verify'),
    path('maintenance/add/', views.add_resident_maintenance_by_admin, name='add_offline_maintenance_payment'),

    path('service_vendors/', views.get_service_vendors, name='get_service_vendors'),
    path('service_vendors/new/', views.add_new_service_vendor, name='add_service_vendor'),
    path('service_vendors/edit/', views.edit_service_vendor, name='edit_service_vendor'),

    path('admins/', views.get_admins, name='get_admins'),
    path('admins/new/', views.add_admins, name='add_admins')

]
