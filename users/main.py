from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ConfigDict, Field

from database import get_db
from models import User


app = FastAPI()


class UserCreate(BaseModel):
    email: str = Field(max_length=255)
    name: str = Field(max_length=255)


class UserRead(UserCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


@app.get("/healthcheck")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"service": "users", "status": "ok"}


@app.post("/users", response_model=UserRead, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(**user.model_dump())
    db.add(new_user)
    try:
        await db.commit()
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="user with this email already exists")


@app.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"user with id {user_id} not found")
    return user

