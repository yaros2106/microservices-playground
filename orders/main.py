import asyncio
import logging

from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from config import settings
from database import get_db
from models import Order


app = FastAPI()
logger = logging.getLogger("uvicorn.error")


class OrderCreate(BaseModel):
    item: str = Field(max_length=255)
    quantity: int


class OrderRead(OrderCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


def get_current_user_id(x_user_id: int = Header()) -> int:
    return x_user_id

@app.get("/healthcheck")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"service": "orders", "status": "ok"}


async def fetch_user(user_id: int) -> httpx.Response:
    attempts = settings.users_retries + 1

    async with httpx.AsyncClient(timeout=settings.users_timeout) as client:
        for attempt in range(1, attempts + 1):
            try:
                response = await client.get(f"{settings.users_url}/users/{user_id}")
            except httpx.RequestError:
                if attempt == attempts:
                    raise
            else:
                if response.status_code < 500 or attempt == attempts:
                    return response
            logger.warning("users call failed, attempt %s of %s", attempt, attempts)
            await asyncio.sleep(0.2)


@app.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(
    order: OrderCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    try:
        response = await fetch_user(user_id)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="users service unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=422, detail=f"user {user_id} not found")
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="users service unavailable")
    new_order = Order(**order.model_dump(), user_id=user_id)
    db.add(new_order)
    await db.commit()
    return new_order



@app.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, order_id)
    if order is None or order.user_id != user_id:
        raise HTTPException(status_code=404, detail=f"order with id {order_id} not found")
    return order


def pagination(limit: int = 10, offset: int = 0):
    return {"limit": limit, "offset": offset}


@app.get("/orders", response_model=list[OrderRead])
async def get_all_orders(
    params: dict = Depends(pagination),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    limit = params["limit"]
    offset = params["offset"]
    stmt = select(Order).where(Order.user_id == user_id).order_by(Order.id).offset(offset).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return orders
