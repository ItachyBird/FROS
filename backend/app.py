from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Flight Optimization API",
    description="API for optimizing flight routes based on weather and other conditions",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import controllers
from controllers.routes_controller import router as routes_router
from controllers.airports_controller import router as airports_router
from controllers.aircraft_controller import router as aircraft_router
from controllers.optimization_controller import router as optimization_router

from realtime import websocket_manager
from realtime import route_adjuster 

# Include routers
app.include_router(routes_router, prefix="/api/routes", tags=["routes"])
app.include_router(airports_router, prefix="/api/airports", tags=["airports"])
app.include_router(aircraft_router, prefix="/api/aircraft", tags=["aircraft"])
app.include_router(optimization_router, prefix="/api/optimize", tags=["optimization"])


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"Request to {request.url.path} processed in {process_time:.4f} seconds"
    )
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "details": str(exc)},
    )


# WebSocket route for real-time updates
@app.websocket("/ws/route/{route_id}")
async def websocket_endpoint(websocket: WebSocket, route_id: str):
    await websocket_manager.connect(route_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()

            # Handle blocked waypoint
            if "block_waypoint" in data:
                waypoint_id = data["waypoint_id"]
                logger.info(f"Waypoint {waypoint_id} blocked on route {route_id}")

                new_route = await route_adjuster.handle_blocked_waypoint(
                    route_id, waypoint_id
                )

                await websocket_manager.broadcast_route_update(route_id, new_route)

    except WebSocketDisconnect:
        await websocket_manager.disconnect(route_id, websocket)
        logger.info(f"Client disconnected from route {route_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        await websocket_manager.disconnect(route_id, websocket)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
