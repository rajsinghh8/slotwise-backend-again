# Numbers router: add numbers with duplicate protection
import os
from dotenv import load_dotenv
load_dotenv('.env_a6b2546857a5b043', override=True)

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import NumberEntry
from app.schemas import NumberCreate, NumberOut

router = APIRouter(tags=["numbers"])


@router.post("/add", response_model=NumberOut, status_code=status.HTTP_201_CREATED)
async def add_number(payload: NumberCreate, db: AsyncSession = Depends(get_db)):
    """Add a number if it does not already exist."""
    result = await db.execute(select(NumberEntry).where(NumberEntry.value == payload.value))
    existing = result.scalar_one_or_none()
    if existing:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": " the given number already exist "},
        )

    number = NumberEntry(value=payload.value)
    db.add(number)
    await db.commit()
    await db.refresh(number)
    return number
