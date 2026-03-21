"""HR Domain Module"""

from app.modules.hr.routes import hr_bp
from app.modules.hr.web_routes import web_hr_bp

__all__ = ["hr_bp", "web_hr_bp"]
