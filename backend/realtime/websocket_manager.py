import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebsocketManager:
    """Manager for WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, route_id: str, websocket: WebSocket):
        """Connect a client to a route's updates."""
        await websocket.accept()

        if route_id not in self.active_connections:
            self.active_connections[route_id] = []

        self.active_connections[route_id].append(websocket)
        logger.info(
            f"Client connected to route {route_id}. Active clients: {len(self.active_connections[route_id])}"
        )

    async def disconnect(self, route_id: str, websocket: WebSocket):
        """Disconnect a client from a route's updates."""
        if route_id in self.active_connections:
            if websocket in self.active_connections[route_id]:
                self.active_connections[route_id].remove(websocket)
                logger.info(
                    f"Client disconnected from route {route_id}. Remaining clients: {len(self.active_connections[route_id])}"
                )

            if len(self.active_connections[route_id]) == 0:
                del self.active_connections[route_id]

    async def broadcast_route_update(self, route_id: str, updated_route: Any):
        """Broadcast updated route to all connected clients."""
        if route_id not in self.active_connections:
            return

        disconnected_sockets = []
        route_dict = (
            updated_route.to_dict()
            if hasattr(updated_route, "to_dict")
            else updated_route
        )

        for websocket in self.active_connections[route_id]:
            try:
                await websocket.send_json({"type": "route_update", "data": route_dict})
            except Exception as e:
                logger.error(f"Error sending to websocket: {str(e)}")
                disconnected_sockets.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected_sockets:
            await self.disconnect(route_id, websocket)

    async def broadcast_waypoint_status(
        self, route_id: str, waypoint_id: str, status: str
    ):
        """Broadcast waypoint status update to all connected clients."""
        if route_id not in self.active_connections:
            return

        disconnected_sockets = []

        for websocket in self.active_connections[route_id]:
            try:
                await websocket.send_json(
                    {
                        "type": "waypoint_status",
                        "data": {"waypoint_id": waypoint_id, "status": status},
                    }
                )
            except Exception as e:
                logger.error(f"Error sending to websocket: {str(e)}")
                disconnected_sockets.append(websocket)

        # Remove disconnected clients
        for websocket in disconnected_sockets:
            await self.disconnect(route_id, websocket)
