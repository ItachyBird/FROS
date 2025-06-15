import logging
import asyncio
from typing import Dict, Any, Optional
import time
from datetime import datetime, timedelta

from models.waypoint import WaypointStatus
from realtime.route_adjuster import RouteAdjuster
from realtime.websocket_manager import WebsocketManager

logger = logging.getLogger(__name__)


class RouteMonitor:
    """Service to monitor routes and detect waypoint status changes."""

    def __init__(
        self,
        route_adjuster: RouteAdjuster,
        websocket_manager: WebsocketManager,
        check_interval: int = 60,
    ):
        self.route_adjuster = route_adjuster
        self.websocket_manager = websocket_manager
        self.check_interval = check_interval  # seconds
        self.monitoring_task = None

    async def start_monitoring(self):
        """Start the background monitoring task."""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitor_routes())
            logger.info("Route monitoring started")

    async def stop_monitoring(self):
        """Stop the background monitoring task."""
        if self.monitoring_task is not None:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("Route monitoring stopped")

    async def _monitor_routes(self):
        """Background task to monitor routes and update waypoint statuses."""
        try:
            while True:
                active_routes = self.route_adjuster.active_routes.copy()
                current_time = datetime.utcnow()

                for route_id, route in active_routes.items():
                    # Skip routes that are too old (e.g., completed)
                    route_age_hours = (
                        current_time - route.created_at
                    ).total_seconds() / 3600
                    if route_age_hours > 24:  # Skip routes older than 24 hours
                        continue

                    # Get current waypoint
                    current_wp = route.get_current_waypoint(current_time)

                    if current_wp:
                        # Update waypoint statuses
                        for waypoint in route.waypoints:
                            if (
                                waypoint.sequence < current_wp.sequence
                                and waypoint.status != WaypointStatus.BLOCKED
                            ):
                                if waypoint.status != WaypointStatus.PASSED:
                                    waypoint.status = WaypointStatus.PASSED
                                    await self.websocket_manager.broadcast_waypoint_status(
                                        route_id,
                                        str(waypoint.id),
                                        WaypointStatus.PASSED,
                                    )
                            elif (
                                waypoint.sequence == current_wp.sequence
                                and waypoint.status != WaypointStatus.BLOCKED
                            ):
                                if waypoint.status != WaypointStatus.ACTIVE:
                                    waypoint.status = WaypointStatus.ACTIVE
                                    await self.websocket_manager.broadcast_waypoint_status(
                                        route_id,
                                        str(waypoint.id),
                                        WaypointStatus.ACTIVE,
                                    )

                # Wait before checking again
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("Route monitoring task cancelled")
        except Exception as e:
            logger.error(f"Error in route monitoring: {str(e)}", exc_info=True)
