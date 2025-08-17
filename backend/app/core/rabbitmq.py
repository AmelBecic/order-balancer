# backend/app/core/rabbitmq.py

import aio_pika
from .config import settings

class RabbitMQ:
    connection: aio_pika.Connection = None
    channel: aio_pika.Channel = None
    orders_exchange: aio_pika.Exchange = None

mq = RabbitMQ()

async def setup_rabbitmq():
    """Declares the necessary exchanges and queues."""
    # Getting a channel
    mq.channel = await mq.connection.channel()

    # Declaring the exchange for orders
    mq.orders_exchange = await mq.channel.declare_exchange(
        "orders_exchange", aio_pika.ExchangeType.TOPIC, durable=True
    )

    # For testing purposes, we'll declare a queue to see messages.
    # In a real worker setup, the worker would declare its own queue.
    processing_queue = await mq.channel.declare_queue(
        "order_processing_queue", durable=True
    )

    # Bind the queue to the exchange to receive new order messages
    await processing_queue.bind(mq.orders_exchange, routing_key="order.new")
    print("RabbitMQ exchanges and queues are set up.")


async def connect_to_rabbitmq():
    """Connects to the RabbitMQ service."""
    print("Connecting to RabbitMQ...")
    mq.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    await setup_rabbitmq() # <-- Call the setup function after connecting
    print("Successfully connected and configured RabbitMQ.")


async def close_rabbitmq_connection():
    """Closes the RabbitMQ connection."""
    print("Closing RabbitMQ connection...")
    if mq.channel:
        await mq.channel.close()
    if mq.connection:
        await mq.connection.close()
    print("RabbitMQ connection closed.")