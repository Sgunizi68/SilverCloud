"""
WSGI Entry Point
For development: python run.py
For production: gunicorn run:app
"""

from app.main import create_main_app

app = create_main_app()

if __name__ == "__main__":
    app.run(debug=True)
