"""API route controllers aggregator."""
from api.routes.chat import router as chat_router
from api.routes.shipment import router as shipment_router
from api.routes.upload import router as upload_router

__all__ = ["chat_router", "shipment_router", "upload_router"]
