from fastapi import APIRouter, Body, status, HTTPException
from app.models.order import OrderCreate, OrderInDB
from app.core.rabbitmq import mq
from app.core.database import get_database
from pymongo.errors import PyMongoError
import aio_pika
import logging
from typing import List
from bson import ObjectId
from bson.errors import InvalidId
from eth_account import Account
from eth_account.messages import encode_defunct

router = APIRouter()

@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Accept a new order for processing",
)
async def create_order(order: OrderCreate = Body(...)):
    # --- SIGNATURE VERIFICATION LOGIC ---
    try:
        formatted_quantity = f"{order.quantity:.6f}" # 6 decimal places
        price_str = f"${order.price:.2f}" if order.price else "Market" # 2 decimal places
        
        message = f"Confirm Order:\n\nAction: {order.side.value.upper()}\nQuantity: {formatted_quantity}\nSymbol: {order.symbol}\nPrice: {price_str}"

        # 2. Encode the message in the same way MetaMask does.
        signable_message = encode_defunct(text=message)

        # 3. Recover the address from the signature.
        recovered_address = Account.recover_message(signable_message, signature=order.signature)

        # 4. Compare the recovered address with the address sent in the payload.
        if recovered_address.lower() != order.address.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signature is invalid or does not match the provided address.",
            )

    except Exception as e:
        logging.error(f"Signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not verify the order signature.",
        )
    # --- END OF VERIFICATION LOGIC ---

    if order.type == "limit" and order.price is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Price must be provided for a limit order.",
        )
    try:
        # The rest of the function remains the same...
        message_body = order.model_dump_json().encode()
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        await mq.orders_exchange.publish(message, routing_key="order.new")
        return {"msg": "Order accepted for processing."}
    except Exception as e:
        logging.error(f"Failed to publish order message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept order.",
        )

# --- GET and DELETE endpoints remain the same ---

@router.get(
    "/",
    response_model=List[OrderInDB],
    summary="Retrieve all orders",
)
async def get_orders():
    db = get_database()
    orders_cursor = db["orders"].find({})
    orders = await orders_cursor.to_list(length=100)
    return orders

@router.delete(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Cancel an existing order",
)
async def cancel_order(order_id: str):
    try:
        obj_id = ObjectId(order_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order ID format: {order_id}",
        )
    db = get_database()
    try:
        delete_result = await db["orders"].delete_one({"_id": obj_id})
        if delete_result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found.",
            )
        return {"msg": f"Order {order_id} cancelled successfully."}
    except PyMongoError as e:
        logging.error(f"Database error while cancelling order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while trying to cancel the order.",
        )
