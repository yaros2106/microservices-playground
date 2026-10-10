from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

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


orders = []


@app.get("/healthcheck")
async def health_check():
    return {"service": "orders", "status": "ok"}


@app.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    new_order = Order(**order.model_dump())
    db.add(new_order)
    await db.commit()
    return new_order


@app.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(order_id: int):
    for order in orders:
        if order["id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail=f"order with id {order_id} not found")


def pagination(limit: int = 10, offset: int = 0):
    return {"limit": limit, "offset": offset}


@app.get("/orders", response_model=list[OrderRead])
async def get_all_orders(params: dict = Depends(pagination)):
    limit = params["limit"]
    offset = params["offset"]
    return orders[offset:limit + offset]
