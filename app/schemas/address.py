import uuid
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# ==========================================
# STATE SCHEMAS
# ==========================================
class StateBase(BaseModel):
    name: str = Field(..., example="Maharashtra")
    code: str = Field(..., min_length=2, max_length=2, example="MH")
    slug: str = Field(..., example="maharashtra")
    is_active: bool = Field(default=True)

class StateCreate(StateBase):
    pass

class StateUpdate(StateBase):
    pass

class StateResponse(StateBase):
    id: uuid.UUID
    
    
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# CITY SCHEMAS
# ==========================================
class CityBase(BaseModel):
    name: str = Field(..., example="Pune")
    slug: str = Field(..., example="pune-mh")
    
    # City needs to link to an existing State ID
    state_id: uuid.UUID = Field(..., example=1) 
    
    pin_code_prefixes: list[str] = Field(default_factory=list, example=["411", "412"])
    city_tier: int = Field(..., ge=1, le=4, example=1, description="Classification tier of the city (1 to 4)")
    is_active: bool = Field(default=True)

class CityCreate(CityBase):
    pass

class CityUpdate(CityBase):
    pass

class CityResponse(CityBase):
    id: uuid.UUID

    
    # Optional: If you want the City response to automatically nest the State data
    # state: StateResponse | None = None
    
    model_config = ConfigDict(from_attributes=True)