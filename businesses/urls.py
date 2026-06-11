from django.urls import path
from .views import RankedBusinessListAPIView

urlpatterns = [
    # Clean API endpoint matching your system structure
    path('businesses/directory/', RankedBusinessListAPIView.as_view(), name='ranked-business-directory'),
]