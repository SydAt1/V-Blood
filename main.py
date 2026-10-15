"""
Main entry point for V-Blood.

Exposes the FastAPI application instance for ASGI servers (e.g. uvicorn main:app).
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment configuration from .env if present
load_dotenv()

# Ensure src/ is on sys.path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from vblood.api.app import create_app

app = create_app()

def main():
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
