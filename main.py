"""Main logic and routing for the FastAPI"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_assistant import assistant
from search import mission_similarity

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

@app.get("/")
async def health() -> str:
    """Sends a 200 response with health back."""
    logger.debug("health check passed")
    return "healthy"