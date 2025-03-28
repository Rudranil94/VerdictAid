from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.services.notification_service import notification_service
from app.core.auth import current_active_user
from app.models.user import User
from app.core.config import settings
import json

router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: int,
    user: User = Depends(current_active_user)
):
    """
    WebSocket endpoint for real-time notifications.
    Requires authentication and maintains user-specific connections.
    """
    if user.id != client_id and not user.is_superuser:
        await websocket.close(code=4003)
        return
    
    try:
        await notification_service.notification_manager.connect(websocket, client_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id
        })
        
        try:
            while True:
                # Listen for client messages (e.g., acknowledgments)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client messages if needed
                if message.get("type") == "ack":
                    # Handle notification acknowledgment
                    pass
                
        except WebSocketDisconnect:
            notification_service.notification_manager.disconnect(websocket, client_id)
            
    except Exception as e:
        await websocket.close(code=1011)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe/email")
async def subscribe_email_notifications(
    preferences: dict,
    user: User = Depends(current_active_user)
):
    """
    Subscribe to email notifications with specific preferences.
    """
    # Update user notification preferences
    user.notification_preferences = {
        **user.notification_preferences,
        "email": preferences
    }
    # Save to database
    return JSONResponse(content={"status": "success"})

@router.post("/subscribe/push")
async def subscribe_push_notifications(
    token: str,
    device_info: dict,
    user: User = Depends(current_active_user)
):
    """
    Subscribe to push notifications for a specific device.
    """
    # Register device token for push notifications
    await notification_service.register_push_device(
        user.id,
        token,
        device_info
    )
    return JSONResponse(content={"status": "success"})

@router.get("/preferences")
async def get_notification_preferences(
    user: User = Depends(current_active_user)
):
    """
    Get user's notification preferences.
    """
    return user.notification_preferences

@router.put("/preferences")
async def update_notification_preferences(
    preferences: dict,
    user: User = Depends(current_active_user)
):
    """
    Update user's notification preferences.
    """
    user.notification_preferences = preferences
    # Save to database
    return JSONResponse(content={"status": "success"})
