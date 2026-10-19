from fastapi import FastAPI, Depends, HTTPException
import httpx
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models import Order

app = FastAPI()


class OrderCreate(BaseModel):
    user_id: int
    item: str = Field(max_length=255)
    quantity: int


class OrderRead(OrderCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


@app.get("/healthcheck")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(1))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"service": "orders", "status": "ok"}



@app.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    try:
        async with httpx.AsyncClient(timeout=settings.users_timeout) as client:
            response = await client.get(f"{settings.users_url}/users/{order.user_id}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="users service unavailable")

    if response.status_code == 404:
        raise HTTPException(status_code=422, detail=f"user {order.user_id} not found")
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="users service unavailable")
    new_order = Order(**order.model_dump())
    db.add(new_order)
    await db.commit()
    return new_order



@app.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"order with id {order_id} not found")
    return order


def pagination(limit: int = 10, offset: int = 0):
    return {"limit": limit, "offset": offset}


@app.get("/orders", response_model=list[OrderRead])
async def get_all_orders(
    params: dict = Depends(pagination),
    db: AsyncSession = Depends(get_db)
):
    limit = params["limit"]
    offset = params["offset"]
    stmt = select(Order).order_by(Order.id).offset(offset).limit(limit)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    return orders
