from django.urls import path
from . import api_views

urlpatterns = [
    path('otp/request', api_views.request_otp, name='request_otp'),
    path('otp/verify', api_views.verify_otp, name='verify_otp'),
]