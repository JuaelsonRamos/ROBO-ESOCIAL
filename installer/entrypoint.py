"""Entrypoint do executável."""

import asyncio
from src import app

if __name__ == "__main__":
    asyncio.run(app())
