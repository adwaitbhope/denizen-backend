from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/new/', views.register_new, name='register_new'),
    path('register/verify/<str:verification_link>/', views.verify_township, name='verify_township'),
    path('register/existing/', views.register_existing, name='register_existing'),
    path('register/check_verification/', views.check_verification, name='check_verification'),
    path('reset_password/', views.send_reset_password_link, name='send_reset_password_link'),
    path('reset_password/<str: reset_password_id>', views.reset_password, name='reset_password'),

    path('payment/paytm/initiate/', views.get_checksumhash, name='init_payment'),
    path('payment/paytm/verify/', views.verify_checksumhash, name='verify_payment'),

    path('complaints/get/', views.get_complaints, name='get_complaints'),
    path('complaints/new/', views.add_complaint, name='add_complaint'),
    path('complaints/resolve/', views.mark_complaint_resolved, name='resolve_complaint'),
]
