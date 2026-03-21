"""Inventory Domain Module"""

from app.modules.inventory.routes import inventory_bp
from app.modules.inventory.web_routes import web_inventory_bp

__all__ = ["inventory_bp", "web_inventory_bp"]
