from django.urls import path
from . import api_views

urlpatterns = [
    # path('token/', api_views.phone_number_token_obtain_pair, name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('otp/request', api_views.request_otp, name='request_otp'),
    path('otp/verify', api_views.verify_otp, name='verify_otp'),
]