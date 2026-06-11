from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.db.models import F, FloatField, ExpressionWrapper, Case, When, Value, Q
from django.db.models.functions import ACos, Cos, Radians, Sin, Least

from .models import Business
from .serializers import BusinessRankedListingSerializer
from .services import geohash_neighbors

class RankedBusinessListAPIView(generics.ListAPIView):
    """
    Returns a composite-scored list of businesses matching a category 
    and localized within the user's geohash neighborhood.
    """
    serializer_class = BusinessRankedListingSerializer
    permission_classes = [AllowAny] # Usually public for directory discovery

    def get_queryset(self):
        # 1. Gather Request Inputs
        user_lat_raw = self.request.query_params.get('lat')
        user_lng_raw = self.request.query_params.get('lng')
        category_slug = self.request.query_params.get('category')

        # Base Filter: Only fetch approved, non-soft-deleted profiles
        queryset = Business.objects.filter(
            status=Business.Status.APPROVED,
            is_active=True
        ).prefetch_related('categories')

        # 2. Apply Category filter if supplied
        if category_slug:
            queryset = queryset.filter(categories__slug=category_slug)

        # 3. Fallback: User denied location permissions or missed coordinates
        if not user_lat_raw or not user_lng_raw:
            return queryset.order_by(
                Case(
                    When(tier=Business.Tier.SPONSORED, then=Value(3)),
                    When(tier=Business.Tier.PRO, then=Value(2)),
                    default=Value(1)
                ),
                '-average_rating',
                '-total_reviews'
            )

        try:
            user_lat = float(user_lat_raw)
            user_lng = float(user_lng_raw)
        except ValueError:
            # Safe recovery fallback if strings are malformed
            return queryset.order_by('-average_rating')

        # -----------------------------------------------------------
        # PHASE A: THE GEOHASH NEIGHBORHOOD FILTER (High Speed)
        # -----------------------------------------------------------
        # Precision 5 creates a geographical bounding box roughly 5km x 5km.
        # Adjust to 6 (~1.2km) if your data density is incredibly tight (e.g., downtown core)
        GEOHASH_PRECISION = 5
        neighborhood_boxes = geohash_neighbors(user_lat, user_lng, precision=GEOHASH_PRECISION)
        # print(f"DEBUG: User Geohash Neighborhood Boxes: {neighborhood_boxes}")

        # Construct a massive SQL "OR" query checking text prefixes:
        # WHERE geohash LIKE 'tupwx%' OR geohash LIKE 'tupwy%' ...
        geohash_query_mask = Q()
        for box in neighborhood_boxes:
            geohash_query_mask |= Q(geohash__startswith=box)
            
        queryset = queryset.filter(geohash_query_mask)

        # -----------------------------------------------------------
        # PHASE B: DISTANCE CALCULATION (Exact Metrics)
        # -----------------------------------------------------------
        # Earth Radius in Kilometers
        EARTH_RADIUS = 6371.0 

        # Spherical Law of Cosines to extract exact decimal distances for UI rendering
        exact_distance_formula = ExpressionWrapper(
            EARTH_RADIUS * ACos(
                Least(
                    Sin(Radians(user_lat)) * Sin(Radians(F('latitude'))) +
                    Cos(Radians(user_lat)) * Cos(Radians(F('latitude'))) *
                    Cos(Radians(F('longitude')) - Radians(user_lng)),
                    1.0 # Protects against float-precision exceptions > 1.0
                )
            ),
            output_field=FloatField()
        )
        queryset = queryset.annotate(distance_kms=exact_distance_formula)

        # -----------------------------------------------------------
        # PHASE C: COMPOSITE ALGORITHM WEIGHTING ENGINE
        # -----------------------------------------------------------
        # Weight 1: Monetization Tiers (Direct boost point values)
        weight_tier = Case(
            When(tier=Business.Tier.SPONSORED, then=Value(100.0)),
            When(tier=Business.Tier.PRO, then=Value(40.0)),
            default=Value(0.0),
            output_field=FloatField()
        )

        # Weight 2: Quality Index (5-Star rating multiplied by a scaling coefficient)
        # A 4.8 star rating yields 48 ranking points
        weight_rating = ExpressionWrapper(
            F('average_rating') * 10.0,
            output_field=FloatField()
        )

        # Weight 3: Proximity Penalty (Further away = subtract points)
        # For every 1 kilometer away, we deduct 5 ranking points
        weight_distance_penalty = ExpressionWrapper(
            F('distance_kms') * 5.0,
            output_field=FloatField()
        )

        # -----------------------------------------------------------
        # PHASE D: FINAL SCORING & SORTATION
        # -----------------------------------------------------------
        # Score Formula = Monetization Boost + Quality Boost - Distance Penalty
        final_score_formula = ExpressionWrapper(
            weight_tier + weight_rating - weight_distance_penalty,
            output_field=FloatField()
        )

        return queryset.annotate(ranking_score=final_score_formula).order_by('-ranking_score')