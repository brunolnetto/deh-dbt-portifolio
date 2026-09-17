"""Extractor — entry point for `python -m extractor`."""
import asyncio
from .main import main

asyncio.run(main())
