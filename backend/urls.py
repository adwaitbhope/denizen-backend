from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('register/new/', views.register_new, name='register_new'),
    path('register/new/certificate/', views.register_certificate, name='register_certificate'),
    path('register/existing/', views.register_existing, name='register_existing')
]
