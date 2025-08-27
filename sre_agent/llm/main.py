"""A server for making requests to an LLM."""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

from sre_agent.llm.utils.clients import (
    AnthropicClient,
    BaseClient,
    DummyClient,
    GeminiClient,
    OpenAIClient,
    SelfHostedClient,
)
from sre_agent.llm.utils.schemas import (
    LLMSettings,
    Provider,
)
from sre_agent.shared.logger import logger
from sre_agent.shared.schemas import Message, TextGenerationPayload

load_dotenv()


STATE: dict[str, BaseClient] = {}


# Lazily instantiate the selected provider to avoid requiring env for all providers
LLM_CLIENT_FACTORY: dict[Provider, Callable[[], BaseClient]] = {
    Provider.ANTHROPIC: lambda: AnthropicClient(),
    Provider.MOCK: lambda: DummyClient(),
    Provider.OPENAI: lambda: OpenAIClient(),
    Provider.GEMINI: lambda: GeminiClient(),
    Provider.SELF_HOSTED: lambda: SelfHostedClient(),
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Any, Any]:
    """A context manager for the REST application.

    On start-up the application will establish an LLM function and settings.
    """
    selected_provider = LLMSettings().provider
    factory = LLM_CLIENT_FACTORY.get(selected_provider, lambda: DummyClient())
    STATE["client"] = factory()

    if STATE["client"] is None:
        supported = ", ".join([p.value for p in Provider])
        raise ValueError(f"Unknown LLM provider. Supported providers are: {supported}")

    yield
    STATE.clear()


app = FastAPI(lifespan=lifespan)


@app.post("/generate")
def generate(payload: TextGenerationPayload) -> Message:
    """An endpoint for generating text from messages and tools."""
    logger.debug(f"Payload: {payload}")

    return STATE["client"].generate(payload)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Health check endpoint for the firewall."""
    return {"status": "healthy"}
