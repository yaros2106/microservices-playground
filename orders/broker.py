import json

import aio_pika
from aio_pika import DeliveryMode, Message

from config import settings

EXCHANGE_NAME = "order-events"


class Broker:
    def __init__(self) -> None:
        self.connection: aio_pika.abc.AbstractRobustConnection | None = None
        self.exchange: aio_pika.abc.AbstractExchange | None = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        channel = await self.connection.channel()
        self.exchange = await channel.declare_exchange(
            EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True
        )

    async def close(self) -> None:
        if self.connection is not None:
            await self.connection.close()

    async def publish(self, routing_key: str, payload: dict) -> None:
        assert self.exchange is not None
        message = Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await self.exchange.publish(message, routing_key=routing_key)


broker = Broker()
