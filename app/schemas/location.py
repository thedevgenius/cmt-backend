from pydantic import BaseModel, Field
from typing import List


class ReverseGeocodeResponse(BaseModel):
    display_name: str

# Autocomplete
class LocationSuggestion(BaseModel):
    # description: str     
    place_id: str         
    main_text: str        
    secondary_text: str  

class AutocompleteResponse(BaseModel):
    suggestions: List[LocationSuggestion]

# Place Detail
class PlaceCoordinatesResponse(BaseModel):
    lat: float
    lng: float


