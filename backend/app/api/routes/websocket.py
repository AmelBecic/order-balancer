# backend/app/api/routes/websocket.py

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from app.core.rabbitmq import mq
from app.api.deps import validate_websocket_origin # <-- Import our new validator

router = APIRouter()

@router.websocket("/ws/orderbook/{symbol}")
async def websocket_orderbook_endpoint(websocket: WebSocket, symbol: str):
    # Perform the origin check before accepting
    is_allowed = validate_websocket_origin(websocket)
    if not is_allowed:
        # If not allowed, close the connection with a policy violation code
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logging.warning(f"Rejected WebSocket connection from invalid origin: {websocket.headers.get('origin')}")
        return

    # If the origin is allowed, accept the connection
    await websocket.accept()
    
    try:
        exchange = await mq.channel.get_exchange("market_data_exchange", ensure=True)
        queue = await mq.channel.declare_queue(exclusive=True)
        
        normalized_symbol = symbol.replace('/', '').lower()
        routing_key = f"orderbook.{normalized_symbol}"
        await queue.bind(exchange, routing_key=routing_key)

        logging.info(f"WebSocket client connected for symbol {symbol}, listening on {routing_key}")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await websocket.send_text(message.body.decode())

    except WebSocketDisconnect:
        logging.info(f"WebSocket client for {symbol} disconnected.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in WebSocket for {symbol}: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)