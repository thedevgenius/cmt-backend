from django.urls import path
from .views import CategoryScrollSpyAPIView, CategoryListAPIView

urlpatterns = [
    path('categories/tree/', CategoryScrollSpyAPIView.as_view(), name='category-scroll-spy'),
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
]