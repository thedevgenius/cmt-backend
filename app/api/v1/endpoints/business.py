from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.category import Category
from app.models.business import Business
from app.core.dependencies import get_db, get_current_user
from app.models.user import User

from app.schemas import business as biz_schemas
from app.services.business import biz_service

router = APIRouter()


@router.post("", response_model=biz_schemas.BizResponse)
async def create_business(
    business_in: biz_schemas.BizCreate,
    db: AsyncSession = Depends(get_db),
    current_user: "User" = Depends(get_current_user) # Injects the logged-in user
):
    # 1. Separate the category_ids from the rest of the business data
    business_data = business_in.model_dump(exclude={"category_ids"})
    
    # 2. Fetch the actual Category objects from the database
    if business_in.category_ids:
        cat_result = await db.execute(
            select(Category).where(Category.id.in_(business_in.category_ids))
        )
        categories = cat_result.scalars().all()
        
        # Security/Validation: Ensure all provided category UUIDs actually exist
        if len(categories) != len(business_in.category_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more provided category IDs are invalid."
            )
    else:
        categories = []

    # 3. Create the Business instance
    # Automatically assign the owner_id from the authenticated user
    new_business = Business(
        **business_data, 
        owner_id=current_user.id 
    )
    
    # 4. Attach the categories (SQLAlchemy handles the association table automatically)
    new_business.categories = list(categories)

    # 5. Save to database
    try:
        db.add(new_business)
        await db.commit()
        await db.refresh(new_business)
    except Exception as e:
        db.rollback()
        # Handle unique constraint violations (e.g., slug already exists)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Error creating business: {str(e)}"
        )

    return new_business