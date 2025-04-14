"""An MCTP SSE Client for interacting with a server using the MCP protocol."""

import logging
import os
from collections import defaultdict
from contextlib import AsyncExitStack
from typing import Any, Dict

from anthropic import Anthropic
from anthropic.types.message_param import MessageParam
from anthropic.types.tool_param import ToolParam
from dotenv import load_dotenv
from fastapi import FastAPI
from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

logger = logging.getLogger(__name__)

CHANNEL_ID = os.getenv("CHANNEL_ID")

if CHANNEL_ID is None:
    raise ValueError("Environment variable CHANNEL_ID is not set.")


# PROMPT = f"""I have an error with my application, can you check the logs for the
# cart service, I only want you to check the pods logs, look up only the 100 most
# recent logs. Feel free to scroll up until you find relevant errors that contain
# reference to a file, once you have these errors and the file name, get the file
# contents of the path src for the repository microservices-demo in the organisation
# fuzzylabs. Keep listing the directories until you find the file name and then get the
# contents of the file. Once you have diagnosed the error please report this to the
# following slack channel: {CHANNEL_ID}."""
#

PROMPT = f"""Can you list pull requests for the microservices-demo repository in the fuzzylabs organisation and then post a message in the slack channel {CHANNEL_ID} with the list of pull requests? Once this is done you can end the conversation."""


class MCPClient:
    """An MCP client for connecting to a server using SSE transport."""

    def __init__(self):
        """Initialize the MCP client and set up the Anthropic API client."""
        self.anthropic = Anthropic()
        self.sessions: Dict[str, Dict] = defaultdict(dict)

    async def __aenter__(self):
        """Set up AsyncExitStack when entering the context manager."""
        self.exit_stack = AsyncExitStack()
        await self.exit_stack.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting the context manager."""
        await self.exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Create and enter the SSE client context
        stream_ctx = sse_client(url=server_url)
        streams = await self.exit_stack.enter_async_context(stream_ctx)

        # Create and enter the ClientSession context
        session = ClientSession(*streams)
        session = await self.exit_stack.enter_async_context(session)

        # Initialize the session
        await session.initialize()

        # List available tools to verify connection
        print(f"Initialized SSE client for {server_url}...")
        print("Listing tools...")
        response = await session.list_tools()
        tools = response.tools
        print(f"\nConnected to {server_url} with tools:", [tool.name for tool in tools])

        self.sessions[server_url] = {"session": session, "tools": tools}

    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query using Claude and available tools"""
        messages = [
            MessageParam(role="user", content=query),
        ]

        available_tools = []

        for service, session in self.sessions.items():
            available_tools.extend(
                [
                    ToolParam(
                        name=tool.name,
                        description=tool.description if tool.description else "",
                        input_schema=tool.inputSchema,
                    )
                    for tool in session["tools"]
                ]
            )

        tool_results = []
        final_text = []
        stop_reason = None

        # Track token usage
        total_input_tokens = 0
        total_output_tokens = 0

        while stop_reason != "end_turn":
            print("Sending request to Claude...")
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
            )
            stop_reason = response.stop_reason

            # Track token usage from this response
            if hasattr(response, "usage"):
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                print(
                    f"Token usage - Input: {response.usage.input_tokens}, Output: {response.usage.output_tokens}"
                )

            for content in response.content:
                if content.type == "text":
                    final_text.append(content.text)
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args: dict[str, Any] = content.input

                    for service, session in self.sessions.items():
                        if tool_name in [tool.name for tool in session["tools"]]:
                            result = await session["session"].call_tool(
                                tool_name, tool_args
                            )
                            break
                    else:
                        raise ValueError(
                            f"Tool {tool_name} not found in available tools."
                        )

                    tool_results.append({"call": tool_name, "result": result})
                    final_text.append(
                        f"[Calling tool {tool_name} with args {tool_args}]"
                    )

                    if hasattr(content, "text") and content.text:
                        messages.append(
                            MessageParam(role="assistant", content=content.text),
                        )
                    messages.append(MessageParam(role="user", content=result.content))

        return {
            "response": "\n".join(final_text),
            "token_usage": {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
            },
        }


app = FastAPI()


@app.get("/diagnose")
async def diagnose():
    async with MCPClient() as client:
        await client.connect_to_sse_server(server_url="http://slack:3001/sse")
        await client.connect_to_sse_server(server_url="http://github:3001/sse")
        await client.connect_to_sse_server(server_url="http://kubernetes:3001/sse")
        result = await client.process_query(PROMPT)
        print(
            f"Token usage - Input: {result['token_usage']['input_tokens']}, "
            f"Output: {result['token_usage']['output_tokens']}, "
            f"Total: {result['token_usage']['total_tokens']}"
        )
        return result
