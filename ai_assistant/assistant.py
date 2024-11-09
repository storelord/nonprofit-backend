"""Main logic and routing for the FastAPI"""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Security, WebSocket
from openai import AsyncOpenAI
from pydantic import ValidationError

from ai_assistant.constants import SYSTEM_PROMPT
from ai_assistant.models.chat_request import ChatRequest
from ai_assistant.models.stream_response import (
    AIResponse,
    AIResponseContent,
    AIResponseError,
    AIResponseSummary,
)
from ai_assistant.security import get_api_key

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="app.log",
)
logger = logging.getLogger(__name__)

router = APIRouter()
client = AsyncOpenAI()


async def ai_response(req: ChatRequest) -> AsyncGenerator[AIResponse, None]:
    """Generates an streamed AI response to the request. Buffers the response to prevent skipped websocket packets in frontend rendering

    Args:
        req (ChatRequest): Information to send to the LLM

    Returns:
        AsyncGenerator[str, None]: None

    Yields:
        Iterator[AsyncGenerator[str, None]]: The generator response with the Response as either Content, Summary, or Error
    """
    sorted_history = sorted(req.history or [], key=lambda x: x.date)
    # Convert the sorted history to the format expected by the OpenAI API
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    messages.extend(
        [{"role": msg.role, "content": msg.message} for msg in sorted_history]
    )

    messages.append(
        {
            "role": "user",
            "content": req.message,
        }
    )

    logger.debug(f"message to openai: {messages}")

    try:
        response = await client.chat.completions.create(
            model=req.model or "gpt-3.5-turbo",
            messages=messages,
            stream=True,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )

        buffer: list[str] = []
        buffer_size = 30
        all_content = ""

        # buffer the web socket or else react can't handle it
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                all_content += content
                buffer.append(content)
                logger.debug(f"delta: {content}")

                if len(buffer) >= buffer_size:
                    yield AIResponseContent(data="".join(buffer))
                    buffer.clear()

        # Add a 100ms delay before sending the summary
        await asyncio.sleep(0.1)
        logger.debug(f"Complete response: {all_content}")
        yield AIResponseSummary(data=all_content)

    except Exception as e:
        logger.exception(f"Failed to generate ai response: {req=}")
        yield AIResponseError(data=str(e))


@router.get("/security_check")
async def security_check(auth=Security(get_api_key)) -> str:
    """
    Websocket for AI responses
    """
    logger.debug("request passed api key security check")
    return "You are welcome"


@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):  # TODO add security dependancy
    """Makes a websocket connection and then listens to recieve a json payload over the socket.
    Responds to the client with streamed text which should be concatonated for the entire message.

    Args:
        websocket (WebSocket): Websocket connection made by FastApi
    """
    await websocket.accept()
    logger.debug("WebSocket connected successfully")

    try:
        while True:
            logger.debug("Waiting for message...")
            data = await websocket.receive_json()
            logger.debug(f"Received raw data: {data}")

            try:
                request = ChatRequest(**data)
                logger.debug(f"Message received: {request.message}")

                async for response in ai_response(request):
                    await websocket.send_json(response.model_dump())

            except json.JSONDecodeError:
                logger.exception("Failed to parse JSON from websocket")
                await websocket.send_json({"error": "Invalid JSON"})
            except ValidationError:
                logger.exception("Data from websocket failed data validation")
                await websocket.send_json(
                    {"error": "Failed to parse request into model"}
                )
    except Exception:
        logger.exception("Unknown error in /ws/chat websocket")
    finally:
        logger.debug("WebSocket connection closed")
