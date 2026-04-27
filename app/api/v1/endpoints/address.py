from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db

from app.schemas import address as address_schemas
from app.services.address import state_service, city_service


router = APIRouter()


@router.post("/states", response_model=address_schemas.StateResponse)
async def create_states( state_in: address_schemas.StateCreate, db: AsyncSession = Depends(get_db)):
    state = await state_service.create(db, obj_in=state_in)
    return state



@router.post("/cities", response_model=address_schemas.CityResponse)
async def create_cities( city_in: address_schemas.CityCreate, db: AsyncSession = Depends(get_db)):
    city = await city_service.create(db, obj_in=city_in)
    return city