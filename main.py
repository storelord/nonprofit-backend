"""Main logic and routing for the FastAPI"""

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_assistant import assistant
from search import mission_similarity

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(assistant.router)
app.include_router(mission_similarity.router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> str:
    """Sends a 200 response with health back. Unauthenticated and used just for checking the server is up.

    Returns:
        str: 'healthy'
    """
    logger.debug("health check passed")
    return "healthy"


def start():
    """Start uvicorn runner. Can be called from file directly or poetry run"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )


if __name__ == "__main__":
    start()
