from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny # Or AllowAny if public
from rest_framework import status

from .serializers import ReverseGeocodeQuerySerializer, AutocompleteQuerySerializer, PlaceCoordinatesQuerySerializer
from .services import get_reverse_geocode, get_location_autocomplete, get_place_coordinates

class ReverseGeocodeView(APIView):
    """
    API View to get a formatted location name from Latitude and Longitude.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Pass request.query_params to the serializer instead of request.data
        serializer = ReverseGeocodeQuerySerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract the validated floats
        lat = serializer.validated_data['lat']
        lng = serializer.validated_data['lng']

        # Call the external service
        result = get_reverse_geocode(lat, lng)

        # Return the appropriate HTTP response
        if result["success"]:
            return Response(result["data"], status=result["status"])
            
        return Response({"detail": result["error"]}, status=result["status"])
    

class LocationAutocompleteView(APIView):
    """
    API View to fetch location predictions based on a partial string.
    """
    # Explicitly set to AllowAny so users don't need a JWT to search locations
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # 1. Validate Query Params
        serializer = AutocompleteQuerySerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Call Service
        q = serializer.validated_data['q']
        result = get_location_autocomplete(q)

        # 3. Return HTTP Response
        if result["success"]:
            return Response(result["data"], status=result["status"])
            
        return Response({"detail": result["error"]}, status=result["status"])
    

class PlaceCoordinatesView(APIView):
    """
    API View to convert a Google place_id into lat/lng coordinates.
    """
    # Set to AllowAny so users can fetch coordinates without being logged in
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # 1. Validate Query Params
        serializer = PlaceCoordinatesQuerySerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. Call Service
        place_id = serializer.validated_data['place_id']
        result = get_place_coordinates(place_id)

        # 3. Return HTTP Response
        if result["success"]:
            return Response(result["data"], status=result["status"])
            
        return Response({"detail": result["error"]}, status=result["status"])