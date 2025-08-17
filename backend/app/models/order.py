# backend/app/models/order.py

from pydantic import BaseModel, Field, BeforeValidator
from enum import Enum
# Make sure 'Annotated' is imported from typing
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"

class OrderBase(BaseModel):
    symbol: str = Field(..., example="BTC/USDT")
    side: OrderSide
    type: OrderType
    quantity: float = Field(..., gt=0) # Must be greater than 0
    price: Optional[float] = Field(None, gt=0) # Required for limit orders

class OrderCreate(OrderBase):
    address: str = Field(..., example="0xAbC...123")
    signature: str = Field(..., example="0x...")

class OrderInDB(OrderBase):
    # We use Annotated to apply a validator *before* Pydantic checks the type.
    # The str() function will convert the ObjectId to a string.
    id: Annotated[str, BeforeValidator(str)] = Field(..., alias="_id")
    status: OrderStatus = Field(default=OrderStatus.OPEN)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    