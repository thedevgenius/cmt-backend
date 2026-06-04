from rest_framework import serializers

class ReverseGeocodeQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(
        min_value=-90, max_value=90, 
        error_messages={"invalid": "Latitude must be a valid number between -90 and 90."}
    )
    lng = serializers.FloatField(
        min_value=-180, max_value=180, 
        error_messages={"invalid": "Longitude must be a valid number between -180 and 180."}
    )

class AutocompleteQuerySerializer(serializers.Serializer):
    q = serializers.CharField(
        min_length=2,
        error_messages={
            "min_length": "Please enter at least 2 characters.",
            "required": "The 'q' parameter is required."
        }
    )


class PlaceCoordinatesQuerySerializer(serializers.Serializer):
    place_id = serializers.CharField(
        required=True,
        error_messages={
            "required": "The 'place_id' parameter is required."
        }
    )