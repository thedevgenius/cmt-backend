import requests, ast
from django.conf import settings
from rest_framework import status
from .models import City

def get_city_details_from_postal_code(postal_code: str) -> dict | None:
    """Return matching city details based on postal code prefix."""

    if not postal_code:
        return None

    cities = City.objects.exclude(pincode_prefix__isnull=True).exclude(pincode_prefix="")

    for city in cities:
        try:
            prefixes = ast.literal_eval(city.pincode_prefix)
            if not isinstance(prefixes, list):
                prefixes = [str(prefixes)]
        except (ValueError, SyntaxError, TypeError):
            prefixes = [p.strip().strip("'\"[]") for p in str(city.pincode_prefix).split(',') if p.strip()]

        if any(postal_code.startswith(str(prefix)) for prefix in prefixes if prefix):
            return {
                "id": city.id,
                "name": getattr(city, "name", "Unknown"),
                "slug": city.slug,
            }

    return None


def get_reverse_geocode(lat: float, lng: float) -> dict:
    """Fetches and formats address components from Google Maps API."""
    
    if not getattr(settings, 'GOOGLE_MAPS_API_KEY', None):
        return {
            "success": False,
            "error": "Google Maps API key is not configured.",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR
        }

    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={settings.GOOGLE_MAPS_API_KEY}"

    try:
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": "Failed to connect to the Geocoding service.",
            "status": status.HTTP_503_SERVICE_UNAVAILABLE
        }

    if not data.get("results"):
        return {
            "success": False,
            "error": "No location data found for these coordinates.",
            "status": status.HTTP_404_NOT_FOUND
        }

    components = data["results"][0].get("address_components", [])
    
    comp_dict = {}
    for comp in components:
        for comp_type in comp["types"]:
            if comp_type not in comp_dict: 
                comp_dict[comp_type] = comp["long_name"]

    desired_order = [
        # "sublocality_level_3",
        # "sublocality_level_2",        
        "sublocality_level_1",         
        "locality",                    
        "administrative_area_level_3", 
        "administrative_area_level_1", 
        # "postal_code",                 
        # "country"                      
    ]

    # Only one of the desired parts should be present
    # display_name = ""
    # for t in desired_order:
    #     if t in comp_dict:
    #         display_name = comp_dict[t]
    #         break  # Stop looking once we find the first available part

    parts = []
    for t in desired_order:
        if t in comp_dict:
            val = comp_dict[t]
            if val not in parts:
                parts.append(val)

    display_name = ", ".join(parts)

    if not display_name:
        display_name = data["results"][0].get("formatted_address", "")

    postal_code = comp_dict.get("postal_code")

    city_details = get_city_details_from_postal_code(postal_code)

    return {
        "success": True,
        "data": {
            "display_name": display_name,
            "postal_code": postal_code,
            "city": city_details
        },
        "status": status.HTTP_200_OK
    }


def get_location_autocomplete(q: str) -> dict:
    """Fetches location predictions from Google Places API."""
    
    if not getattr(settings, 'GOOGLE_MAPS_API_KEY', None):
        return {
            "success": False,
            "error": "Google Maps API key is not configured.",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR
        }

    # Restricting results to India (country:in) as per your original code
    url = (
        f"https://maps.googleapis.com/maps/api/place/autocomplete/json"
        f"?input={q}"
        f"&components=country:in"
        f"&key={settings.GOOGLE_MAPS_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": "Failed to connect to the Autocomplete service.",
            "status": status.HTTP_503_SERVICE_UNAVAILABLE
        }

    if data.get("status") not in ["OK", "ZERO_RESULTS"]:
        return {
            "success": False,
            "error": f"Google API Error: {data.get('status')}",
            "status": status.HTTP_400_BAD_REQUEST
        }

    suggestions = []
    
    # Format Google's response into a clean dictionary
    for prediction in data.get("predictions", []):
        formatting = prediction.get("structured_formatting", {})
        
        suggestions.append({
            "place_id": prediction.get("place_id"),
            "main_text": formatting.get("main_text", ""),
            "secondary_text": formatting.get("secondary_text", "")
        })

    return {
        "success": True,
        "data": {"suggestions": suggestions},
        "status": status.HTTP_200_OK
    }


def get_place_coordinates(place_id: str) -> dict:
    """Converts a Google place_id into usable lat/lng coordinates."""
    
    if not getattr(settings, 'GOOGLE_MAPS_API_KEY', None):
        return {
            "success": False,
            "error": "Google Maps API key is not configured.",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR
        }

    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?place_id={place_id}"
        f"&key={settings.GOOGLE_MAPS_API_KEY}"
    )

    try:
        response = requests.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return {
            "success": False,
            "error": "Failed to connect to the Geocoding service.",
            "status": status.HTTP_503_SERVICE_UNAVAILABLE
        }

    if not data.get("results"):
        return {
            "success": False,
            "error": "Coordinates not found for this location.",
            "status": status.HTTP_404_NOT_FOUND
        }

    # Extract the nested lat/lng data safely
    result = data["results"][0]
    
    # Extract the nested lat/lng data safely
    location = result["geometry"]["location"]
    
    # --- NEW: Extract Postal Code ---
    components = result.get("address_components", [])
    postal_code = None
    
    for comp in components:
        if "postal_code" in comp.get("types", []):
            postal_code = comp.get("long_name")
            break

    # --- NEW: Match Postal Code to City ---
    city_details = get_city_details_from_postal_code(postal_code)

    return {
        "success": True,
        "data": {
            "lat": location["lat"],
            "lng": location["lng"],
            "postal_code": postal_code,
            "city": city_details
        },
        "status": status.HTTP_200_OK
    }
