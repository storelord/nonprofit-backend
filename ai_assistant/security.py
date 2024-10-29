"""Security Middleware"""

import logging
import os
from secrets import compare_digest

from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

logger = logging.getLogger(__name__)

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "X-API-Key"

if API_KEY is None:
    logger.critical("API_KEY is not set in environment!")


async def get_api_key(
    api_key_header: str = Security(APIKeyHeader(name=API_KEY_NAME, auto_error=False)),
) -> None:
    """Middleware for checking that the incomin request matches a api key

    Args:
        api_key_header: Parameters used by FastAPI to parse http request coming in

    Raises:
        HTTPException: If the api key is not found or doesn't match

    Returns:
        None: Passes nothing onto the next function
    """
    if api_key_header is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="api key not found in header"
        )
    if compare_digest(api_key_header, API_KEY):
        return None
    else:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Could not validate API key"
        )
