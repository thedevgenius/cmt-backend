from django.urls import path
from .views import CategoryScrollSpyAPIView

urlpatterns = [
    path('categories/scroll-spy/', CategoryScrollSpyAPIView.as_view(), name='category-scroll-spy'),
]