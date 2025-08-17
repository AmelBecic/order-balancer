# backend/app/api/deps.py

from fastapi import WebSocket, HTTPException, status
from app.core.config import settings

def validate_websocket_origin(websocket: WebSocket):
    """
    Checks if the WebSocket connection's origin is in the allowed list.
    """
    origin = websocket.headers.get("origin")
    if origin not in settings.BACKEND_CORS_ORIGINS:
        # Note: You can't raise HTTPException in a WebSocket,
        # but this check happens before the connection is accepted.
        # A more robust way is to close the connection with a code.
        # For now, this logic will prevent the `accept()` call.
        # A proper close is handled in the main endpoint.
        return False
    return True