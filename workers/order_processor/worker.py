# workers/order_processor/worker.py

import asyncio
import json
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import aio_pika

# Local imports for the worker
from config import settings
from matching_engine import MatchingEngine

# The name of the queue this worker will consume from
QUEUE_NAME = "order_processing_queue"

# Setup basic logging
logging.basicConfig(level=logging.INFO)


async def process_message(message: aio_pika.IncomingMessage, db_client: AsyncIOMotorClient, engine: MatchingEngine):
    """
    This is the callback function that gets executed for each message.
    """
    # Acknowledge the message so RabbitMQ knows it's been processed
    async with message.process():
        try:
            body = message.body.decode()
            order_data = json.loads(body)
            logging.info(f"Worker received order: {order_data}")
            
            # The worker's only job is to pass the validated order to the engine
            await engine.process_order(order_data, db_client[settings.DATABASE_NAME])

        except Exception as e:
            logging.error(f"Worker failed to process message: {e}")


async def main():
    """Main function to set up connections and start the worker."""
    # Connect to MongoDB using the URL from our settings
    db_client = AsyncIOMotorClient(settings.MONGODB_URL)
    logging.info("Connected to MongoDB.")

    # Initialize the Matching Engine
    engine = MatchingEngine()
    
    # Connect to RabbitMQ using the URL from our settings
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)

    # This 'async with' block ensures connections are closed gracefully
    async with connection:
        channel = await connection.channel()
        
        # Declare the queue for consuming new orders
        order_queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        
        # Declare the exchange for broadcasting market data updates
        market_data_exchange = await channel.declare_exchange(
            "market_data_exchange", aio_pika.ExchangeType.TOPIC, durable=True
        )
        
        # Give the engine a reference to this exchange so it can publish updates
        engine.set_market_data_exchange(market_data_exchange)
        
        # Load existing orders from the database into the engine's memory on startup
        await engine.load_orders_from_db(db_client[settings.DATABASE_NAME])
        
        logging.info("Worker is waiting for messages...")
        
        # Start consuming messages from the queue and passing them to our callback
        await order_queue.consume(lambda message: process_message(message, db_client, engine))

        # This is the critical line that keeps the worker running forever
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker stopped.")