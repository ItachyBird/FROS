# Import realtime components for easy access
from realtime.websocket_manager import WebsocketManager
from realtime.route_monitor import RouteMonitor
from realtime.route_adjuster import RouteAdjuster

# Create shared instances
websocket_manager = WebsocketManager()
route_adjuster = RouteAdjuster()
route_monitor = RouteMonitor(route_adjuster, websocket_manager)
