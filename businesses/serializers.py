from rest_framework import serializers
from .models import Business

class BusinessRankedListingSerializer(serializers.ModelSerializer):
    # Dynamic field injected by the view's query annotations
    distance_kms = serializers.FloatField(read_only=True, required=False)
    ranking_score = serializers.FloatField(read_only=True, required=False)
    category_names = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'slug', 'description', 'tier',
            'average_rating', 'total_reviews', 'view_count',
            'address_line_1', 'city', 'postal_code',
            'latitude', 'longitude', 'distance_kms', 'ranking_score',
            'category_names', 'created_at'
        ]

    def get_category_names(self, obj):
        return [category.name for category in obj.categories.all()]