"""Main logic and routing for the FastAPI"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
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

@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "message": "Oops! The resource you are looking for does not exist.",
                "url": str(request.url)
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail, "url": str(request.url)}
    )
