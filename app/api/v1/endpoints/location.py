import httpx
from fastapi import APIRouter, HTTPException, status, Query
from app.schemas import location as location_schema
from app.core.config import settings

router = APIRouter()

@router.get("/geocode/reverse", response_model=location_schema.ReverseGeocodeResponse)
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90, description="Latitude between -90 and 90"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude between -180 and 180")
):
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Maps API key is not configured."
        )
    
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={settings.GOOGLE_MAPS_API_KEY}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError:
             raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to the Geocoding service."
            )

    if not data.get("results"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No location data found for these coordinates."
        )

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
        "postal_code",                 
        "country"                      
    ]

    parts = []
    for t in desired_order:
        if t in comp_dict:
            val = comp_dict[t]
            if val not in parts:
                parts.append(val)

    display_name = ", ".join(parts)

    if not display_name:
        display_name = data["results"][0].get("formatted_address", "")

    return {
        "display_name": display_name,
    }


@router.get("/autocomplete", response_model=location_schema.AutocompleteResponse)
async def location_autocomplete(
    # Require at least 2 characters before hitting Google to save on API costs
    q: str = Query(..., min_length=2, description="The partial location string"),
):
    """
    Fetches location predictions (Cities, Neighborhoods) from Google Places API 
    based on user input.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Maps API key is not configured."
        )

    # We use types=(regions) to restrict results to cities, neighborhoods, and states
    url = (
        f"https://maps.googleapis.com/maps/api/place/autocomplete/json"
        f"?input={q}"
        # f"&types=(regions)"
        f"&components=country:in"
        f"&key={settings.GOOGLE_MAPS_API_KEY}"
    )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError:
             raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to the Autocomplete service."
            )

    if data.get("status") != "OK" and data.get("status") != "ZERO_RESULTS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google API Error: {data.get('status')}"
        )

    suggestions = []
    
    # Format Google's messy response into our clean Pydantic schema
    for prediction in data.get("predictions", []):
        formatting = prediction.get("structured_formatting", {})
        
        suggestions.append(location_schema.LocationSuggestion(
            # description=prediction.get("description"),
            place_id=prediction.get("place_id"),
            main_text=formatting.get("main_text", ""),
            secondary_text=formatting.get("secondary_text", "")
        ))

    return {"suggestions": suggestions}


@router.get("/coordinates", response_model=location_schema.PlaceCoordinatesResponse)
async def get_place_coordinates(
    place_id: str = Query(..., description="The Google place_id from the autocomplete API")
):
    """
    Converts a Google place_id into usable lat/lng coordinates for spatial searching.
    """
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?place_id={place_id}"
        f"&key={settings.GOOGLE_MAPS_API_KEY}"
    )

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    if not data.get("results"):
        raise HTTPException(status_code=404, detail="Coordinates not found for this location.")

    location = data["results"][0]["geometry"]["location"]
    
    return {
        "lat": location["lat"],
        "lng": location["lng"]
    }