# backend/app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
import aio_pika
from fastapi.middleware.cors import CORSMiddleware

# Local imports for the backend API
from app.core.rabbitmq import connect_to_rabbitmq, close_rabbitmq_connection, mq
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import orders, websocket
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    """
    # Code to run on startup
    await connect_to_mongo()
    await connect_to_rabbitmq()
    
    # To be safe, ensure the market data exchange exists from the API side too.
    await mq.channel.declare_exchange(
        "market_data_exchange", aio_pika.ExchangeType.TOPIC, durable=True
    )

    yield # The application runs while in the 'yield'

    # Code to run on shutdown
    await close_mongo_connection()
    await close_rabbitmq_connection()


# Create the main FastAPI application instance
app = FastAPI(
    title="Order Balancer API",
    lifespan=lifespan
)

# Add the CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS, # <-- CHANGE THIS LINE BACK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Order Balancer API!"}


# Include the API routers for different functionalities
app.include_router(orders.router, prefix=f"{settings.API_V1_STR}/orders", tags=["Orders"])
app.include_router(websocket.router, prefix=f"{settings.API_V1_STR}", tags=["WebSockets"])