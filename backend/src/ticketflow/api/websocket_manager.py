"""
WebSocket manager for real-time communication
Enables live demo of agent processing
"""

import json
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup WebSocket routes"""
        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.connect(websocket)
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self.handle_message(websocket, message)
            except WebSocketDisconnect:
                self.disconnect(websocket)
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to TicketFlow AI",
            "timestamp": asyncio.get_event_loop().time()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket"""
        if websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        message_str = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(message_str)
                else:
                    disconnected.append(connection)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn)
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        message_type = message.get("type")
        
        if message_type == "ping":
            await self.send_personal_message({"type": "pong"}, websocket)
        elif message_type == "subscribe":
            # Handle subscription to specific events
            await self.send_personal_message({
                "type": "subscribed",
                "subscription": message.get("subscription")
            }, websocket)
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    async def send_agent_update(self, ticket_id: int, step: str, message: str, data: Dict[str, Any] = None):
        """Send agent processing update"""
        update = {
            "type": "agent_update",
            "ticket_id": ticket_id,
            "step": step,
            "message": message,
            "data": data or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_ticket_created(self, ticket_data: Dict[str, Any]):
        """Send ticket created notification"""
        notification = {
            "type": "ticket_created",
            "ticket": ticket_data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(notification)
    
    async def send_metrics_update(self, metrics: Dict[str, Any]):
        """Send metrics update"""
        update = {
            "type": "metrics_update",
            "metrics": metrics,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_learning_update(self, learning_metrics: Dict[str, Any]):
        """Send learning metrics update for live broadcast"""
        update = {
            "type": "learning_update",
            "learning_metrics": learning_metrics,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_workflow_status(self, workflow_id: int, status: str, progress: float = None):
        """Send workflow status update for live broadcast"""
        update = {
            "type": "workflow_status",
            "workflow_id": workflow_id,
            "status": status,
            "progress": progress,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_agent_decision(self, ticket_id: int, decision: str, confidence: float, reasoning: str):
        """Send agent decision update for live broadcast"""
        update = {
            "type": "agent_decision",
            "ticket_id": ticket_id,
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_resolution_update(self, ticket_id: int, resolution_type: str, confidence: float, resolution_text: str = None):
        """Send resolution update for live broadcast"""
        update = {
            "type": "resolution_update",
            "ticket_id": ticket_id,
            "resolution_type": resolution_type,
            "confidence": confidence,
            "resolution_text": resolution_text,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_feedback_processed(self, workflow_id: int, feedback_summary: Dict[str, Any]):
        """Send feedback processing update for live broadcast"""
        update = {
            "type": "feedback_processed",
            "workflow_id": workflow_id,
            "feedback_summary": feedback_summary,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
    async def send_system_status(self, status: str, message: str, details: Dict[str, Any] = None):
        """Send system status update for live broadcast"""
        update = {
            "type": "system_status",
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(update)
    
# Global WebSocket manager instance
websocket_manager = WebSocketManager()