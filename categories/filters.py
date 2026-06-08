from django_filters import rest_framework as filters
from .models import Category

class CategoryFilter(filters.FilterSet):
    # Allows ?is_root=true to get only top-level categories
    is_root = filters.BooleanFilter(field_name='parent', lookup_expr='isnull')
    
    # Allows filtering by specific parent ID (e.g., ?parent=5)
    parent = filters.NumberFilter(field_name='parent_id')

    class Meta:
        model = Category
        fields = ['parent', 'is_active', 'is_featured']