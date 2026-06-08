from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch
from rest_framework.permissions import AllowAny # Or AllowAny if public
from .models import Category
from .serializers import CategoryRootSerializer, CategoryListSerializer
from .pagination import StandardResultsSetPagination
from .filters import CategoryFilter


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

class CategoryListAPIView(generics.ListAPIView):
    """
    API endpoint to list categories with search, filtering, and ordering.
    """
    permission_classes = [AllowAny]
    serializer_class = CategoryListSerializer
    pagination_class = StandardResultsSetPagination
    
    # 1. DjangoFilterBackend handles exact matches (parent, is_active)
    # 2. SearchFilter handles fuzzy text searches
    # 3. OrderingFilter handles sorting
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    # Setup exact field filters
    filterset_class = CategoryFilter
    
    # Setup search (e.g., ?search=plumbing)
    search_fields = ['name', 'description', 'slug']
    
    # Setup ordering (e.g., ?ordering=-created_at or ?ordering=name)
    ordering_fields = ['name', 'sort_order', 'created_at', 'updated_at']
    
    # Default ordering (matches your model's Meta ordering)
    ordering = ['sort_order', 'name']

    def get_queryset(self):
        # select_related optimizes the query by fetching the parent category 
        # in the same SQL hit, preventing N+1 queries when serializing parent_name.
        return Category.objects.select_related('parent').filter(is_active=True)