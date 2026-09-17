"""OLTP API — entry point for `python -m oltp_api`."""
import uvicorn
from .main import app

uvicorn.run(app, host="0.0.0.0", port=8001)
