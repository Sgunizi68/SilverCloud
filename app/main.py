"""
Main Flask Application Entry Point
"""

from flask import Flask


def create_main_app() -> Flask:
    """
    Create and configure the main Flask application.
    
    Returns:
        Configured Flask app instance
    """
    from app import create_app
    
    app = create_app(config_name="development")
    
    @app.route("/", methods=["GET"])
    def index():
        """Health check endpoint"""
        return {"status": "ok", "message": "SilverCloud API running"}, 200
    
    @app.route("/health", methods=["GET"])
    def health():
        """Health check for monitoring"""
        return {"status": "healthy"}, 200
    
    return app


if __name__ == "__main__":
    app = create_main_app()
    app.run(host="0.0.0.0", port=5000)
