from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate

def index(request):
    return HttpResponse("Hello, world. You're at the index.")

def login(request):
    username = request.GET['username']
    password = request.GET['password']

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse([{'login': 0}], safe=False)
    return JsonResponse([{'login': 1}], safe=False)
