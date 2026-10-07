from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class OrderCreate(BaseModel):
    user_id: int
    item: str
    quantity: int


orders = []


@app.get("/healthcheck")
async def health_check():
    return {"service": "orders", "status": "ok"}


@app.post("/orders")
async def create_order(order: OrderCreate):
    new_id = len(orders) + 1
    new_order = {"id": new_id, **order.model_dump()}
    orders.append(new_order)
    return new_order


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    for order in orders:
        if order["id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail=f"order with id {order_id} not found")
