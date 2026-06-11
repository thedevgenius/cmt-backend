from django.urls import path
from .views import CentralImageUploadAPIView

urlpatterns = [
    path('upload/image/', CentralImageUploadAPIView.as_view(), name='central-image-upload'),
]