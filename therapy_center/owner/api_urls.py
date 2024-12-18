from django.urls import path
from . import api_views

urlpatterns = [
    path(route='home/',view=api_views.home, name='owner-home'),

]