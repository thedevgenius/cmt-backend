from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserProfileAPIView, RequestOTPView, VerifyOTPView

app_name = 'users' 

urlpatterns = [
    path('users/me/', UserProfileAPIView.as_view(), name='profile_view'),
    path('otp/request/', RequestOTPView.as_view(), name='request_otp'),
    path('otp/verify/', VerifyOTPView.as_view(), name='verify_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]