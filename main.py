"""
Main entry point for V-Blood.

Exposes the FastAPI application instance for ASGI servers (e.g. uvicorn main:app).
"""

from vblood.api.app import create_app

app = create_app()

def main():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
