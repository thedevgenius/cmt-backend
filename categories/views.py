from rest_framework import generics
from django.db.models import Prefetch
from .models import Category
from .serializers import CategoryRootSerializer
from rest_framework.permissions import AllowAny # Or AllowAny if public

class CategoryScrollSpyAPIView(generics.ListAPIView):
    serializer_class = CategoryRootSerializer
    
    # CRITICAL: Disable pagination for this specific endpoint. 
    # The frontend needs the entire tree at once to calculate scroll heights.
    pagination_class = None 
    permission_classes = [AllowAny]

    def get_queryset(self):
        # 1. Create a base queryset for children to ensure we respect ordering 
        #    and only fetch active sub-categories.
        active_children = Category.objects.filter(
            is_active=True
        ).order_by('sort_order', 'name')

        # 2. Query root categories and prefetch exactly 2 levels deep
        queryset = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).prefetch_related(
            # Fetches Level 2
            Prefetch('children', queryset=active_children),
            # Fetches Level 3 
            Prefetch('children__children', queryset=active_children) 
        ).order_by('sort_order', 'name')

        return queryset