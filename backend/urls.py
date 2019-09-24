from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/new/', views.register_new, name='register_new'),
    path('register/verify/<str:verification_link>/', views.verify_township, name='verify_township'),
    path('register/existing/', views.register_existing, name='register_existing'),
    path('register/check_verification/', views.check_verification, name='check_verification'),
]
