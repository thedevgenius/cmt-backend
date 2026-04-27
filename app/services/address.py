from app.services.base import BaseService
from app.models.address import State, City
from app.schemas.address import StateCreate, StateUpdate, CityCreate, CityUpdate

class StateService(BaseService[State, StateCreate, StateUpdate]):
    pass

class CityService(BaseService[City, CityCreate, CityUpdate]):
    pass


state_service = StateService(State)
city_service = CityService(City)