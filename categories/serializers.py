from rest_framework import serializers
from .models import Category

class CategoryGrandchildSerializer(serializers.ModelSerializer):
    """Level 3: Indian, Italian, Plumbers"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class CategoryChildSerializer(serializers.ModelSerializer):
    """Level 2: Restaurant, Cafe, Clinic"""
    # Map the reverse relation 'children' to the grandchild serializer
    children = CategoryGrandchildSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'children']

class CategoryRootSerializer(serializers.ModelSerializer):
    """Level 1: Food & Restaurants, Medical, Home Services"""
    # Map the reverse relation 'children' to the child serializer
    children = CategoryChildSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'children']