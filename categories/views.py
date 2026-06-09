import hashlib
from django.core.cache import cache
from rest_framework import generics
from rest_framework.response import Response
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
    pagination_class = None 
    permission_classes = [AllowAny]

    def get_queryset(self):
        active_children = Category.objects.filter(
            is_active=True
        ).order_by('sort_order', 'name')

        queryset = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).prefetch_related(
            Prefetch('children', queryset=active_children),
            Prefetch('children__children', queryset=active_children) 
        ).order_by('sort_order', 'name')

        return queryset

    def list(self, request, *args, **kwargs):
        # 1. Define a static key since this response is exactly the same for all users
        cache_key = 'category_scroll_spy_tree'

        # 2. Check Redis for the data
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            # REDIS HIT: Return the massive JSON tree instantly
            return Response(cached_data)

        # 3. REDIS MISS: Let DRF execute the heavy get_queryset() and serialization
        response = super().list(request, *args, **kwargs)

        # 4. Save to Redis infinitely (timeout=None)
        cache.set(cache_key, response.data, timeout=None)

        return response

class CategoryListAPIView(generics.ListAPIView):
    """
    API endpoint to list categories with search, filtering, and ordering.
    """
    permission_classes = [AllowAny]
    serializer_class = CategoryListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description', 'slug']
    ordering_fields = ['name', 'sort_order', 'created_at', 'updated_at']
    ordering = ['sort_order', 'name']
    
    def get_queryset(self):
        return Category.objects.select_related('parent').filter(is_active=True)

    def list(self, request, *args, **kwargs):
        # 1. Grab the raw query string (e.g., "search=plumbing&page=2")
        query_string = request.META.get('QUERY_STRING', '')
        
        # 2. Hash it to create a short, safe, unique string for Redis
        query_hash = hashlib.md5(query_string.encode('utf-8')).hexdigest()
        
        # 3. Create the final cache key
        cache_key = f"category_list_query_{query_hash}"

        # 4. Attempt to get the response data from Redis
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return Response(cached_data)

        # 5. REDIS MISS: Let DRF handle the database query, filtering, and pagination
        response = super().list(request, *args, **kwargs)

        # 6. Save the paginated dictionary (response.data) to Redis.
        # We set a shorter TTL here (e.g., 1 hour) because search results 
        # can take up a lot of memory if users search random strings.
        cache.set(cache_key, response.data, timeout=60 * 60)
        return response