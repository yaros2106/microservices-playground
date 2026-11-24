import asyncio
import json
import logging
from contextlib import asynccontextmanager, suppress

import aio_pika
from fastapi import FastAPI

from config import settings

logger = logging.getLogger("uvicorn.error")

EXCHANGE_NAME = "order-events"
QUEUE_NAME = "notifications.order-created"
ROUTING_KEY = "order.created"


async def consume() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.bind(exchange, routing_key=ROUTING_KEY)
        logger.info("listening on queue %s", QUEUE_NAME)

        async with queue.iterator() as messages:
            async for message in messages:
                async with message.process():
                    data = json.loads(message.body)
                    logger.info(
                        "email sent: order %s (user %s)",
                        data.get("order_id"),
                        data.get("user_id"),
                    )


async def run_consumer() -> None:
    while True:
        try:
            await consume()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("consumer failed, retrying in 5 seconds")
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_consumer())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(lifespan=lifespan)


@app.get("/healthcheck")
async def health_check():
    return {"service": "notifications", "status": "ok"}
