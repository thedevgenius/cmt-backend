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
                "name": getattr(city, "name", "Unknown"),
                "slug": city.slug,
            }

    return None


def extract_best_landmark(address_dict):
    """
    Extracts the most specific location identifier from a Nominatim address dictionary.
    Falls back to broader regions if the specific local tags are missing.
    """
    if not address_dict:
        return None

    # Ordered from most specific (local) to least specific (regional)
    # Note: Added 'neighbourhood', 'village', and 'city' as OSM frequently 
    # uses these depending on population density.
    hierarchy = [
        'suburb',
        'neighbourhood',
        'village',
        'town',
        'city',
        'municipality',
        'county',
        'state_district'
    ]

    for key in hierarchy:
        landmark = address_dict.get(key)
        if landmark:
            return landmark

    # Absolute fallback if somehow none of the above exist
    return address_dict.get('state', 'Unknown Location')


def get_city_by_lat_lng(lat: float, lng: float) -> dict | None:
    """Fetches city details based on latitude and longitude using Nominatim."""
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&zoom=14&format=json"
    headers = {
        'User-Agent': 'Comynity/1.0'
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        address_dict = data.get('address', {})
        postal_code = address_dict.get('postcode')
        if not postal_code:
            city = address_dict.get('city') or address_dict.get('state_district')
            if city:
                return {"name": city, "slug": city.lower().replace(" ", "-")}
            else:
                return None
        return get_city_details_from_postal_code(postal_code)

    except requests.exceptions.RequestException:
        return None


def get_reverse_geocode(lat: float, lng: float, provider: str = "google") -> dict:  
    """Fetches and formats address components from Google Maps API."""
    provider = provider.lower()

    if provider == "google":
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
        ]

        # Only one of the desired parts should be present
        display_name = ""
        for t in desired_order:
            if t in comp_dict:
                display_name = comp_dict[t]
                break

        if not display_name:
            display_name = data["results"][0].get("formatted_address", "")
        
        city_details = get_city_by_lat_lng(lat, lng)

        return {
            "success": True,
            "data": {
                "landmark": display_name,
                "city": city_details
            },
            "status": status.HTTP_200_OK
        }

    if provider == "nominatim":
        # Implement Nominatim reverse geocoding logic here if needed
        headers = {
            'User-Agent': 'Comynity/1.0'
        }
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&zoom=14&format=json"

        try:
            # 2. Make the HTTP Request
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            data = response.json()
            address_dict = data.get('address', {})

            # 3. Apply your fallback logic
            best_landmark = extract_best_landmark(address_dict)
            postal_code = address_dict.get('postcode')

            return {
                "success": True,
                "landmark": best_landmark,
                "status": status.HTTP_200_OK
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Geocoding request failed: {str(e)}",
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
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
    city_details = get_city_by_lat_lng(location["lat"], location["lng"])

    return {
        "success": True,
        "data": {
            "lat": location["lat"],
            "lng": location["lng"],
            "city": city_details
        },
        "status": status.HTTP_200_OK
    }
