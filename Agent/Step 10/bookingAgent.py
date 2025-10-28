from livekit.agents.llm import function_tool
from livekit.agents import Agent
from prompts import BOOKING_INSTRUCTIONS
from OEDatabaseDriver import Car
from typing import Annotated, Any
from dataclasses import asdict
from datetime import date
import logging
import asyncio
import sys
import os
from pathlib import Path
from livekit.plugins import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import inspect

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)


class BookingAssistant(Agent):
    """
    Booking assistant that uses MCP server for booking operations.
    Dynamically discovers and exposes tools from the MCP server - NO HARD-CODED TOOLS!
    """

    def __init__(self, car: Car) -> None:
        self.car = car
        self._mcp_session: ClientSession | None = None
        self._mcp_tools: dict[str, Any] = {}
        self._server_params = None
        self._stdio_transport = None

        # CRITICAL: Discover and inject MCP tools BEFORE calling super().__init__()
        # This allows LiveKit to find them during agent initialization
        self._setup_dynamic_tools()

        super().__init__(
            instructions=BOOKING_INSTRUCTIONS,
            llm=openai.realtime.RealtimeModel(
                voice="echo",
                temperature=0.8
            )
        )

    def _setup_dynamic_tools(self):
        """
        Discover MCP tools and dynamically create function_tool methods.
        This is the magic that makes MCP truly powerful!
        """
        try:
            # Initialize MCP connection parameters
            server_path = Path(__file__).parent / "bookings_mcp" / "server.py"
            self._server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(server_path)],
                env={**os.environ}
            )

            # Connect to MCP and discover tools
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # Already in async context - create a task
                import nest_asyncio
                nest_asyncio.apply()
                tools = loop.run_until_complete(self._discover_mcp_tools())
            except RuntimeError:
                # No running loop - create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    tools = loop.run_until_complete(self._discover_mcp_tools())
                finally:
                    loop.close()

            logger.info(f"[MCP] Discovered {len(tools)} MCP tools: {[t.name for t in tools]}")

            # Dynamically create a function_tool method for each MCP tool
            for tool in tools:
                self._create_dynamic_tool(tool)
                logger.info(f"[MCP] Dynamically registered: {tool.name}")

        except Exception as e:
            logger.error(f"Failed to setup dynamic MCP tools: {e}")
            raise

    async def _discover_mcp_tools(self):
        """Connect to MCP server and list available tools"""
        stdio_transport = stdio_client(self._server_params)
        stdio, write = await stdio_transport.__aenter__()
        session = ClientSession(stdio, write)
        await session.__aenter__()
        await session.initialize()

        # Get tool list
        tools_result = await session.list_tools()

        # Store for later use
        self._mcp_tools = {tool.name: tool for tool in tools_result.tools}

        # Clean up this discovery session
        await session.__aexit__(None, None, None)
        await stdio_transport.__aexit__(None, None, None)

        return tools_result.tools

    def _create_dynamic_tool(self, mcp_tool):
        """
        Dynamically create a LiveKit function_tool from an MCP tool definition.
        This is where the dynamic magic happens!
        """
        tool_name = mcp_tool.name
        tool_description = mcp_tool.description
        tool_schema = mcp_tool.inputSchema

        # Parse parameters from MCP schema
        properties = tool_schema.get("properties", {})
        required = tool_schema.get("required", [])

        # Build function signature dynamically
        params = []
        annotations = {}

        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")

            # Skip 'reg' parameter - we'll inject it automatically
            if param_name == "reg":
                continue

            # Map JSON schema types to Python types
            if param_type == "string":
                # Check if it's a date by parameter name or description
                if "date" in param_name.lower() or "date" in param_desc.lower():
                    python_type = date
                else:
                    python_type = str
            elif param_type == "integer":
                python_type = int
            elif param_type == "number":
                python_type = float
            else:
                python_type = str

            # Create annotated parameter
            annotations[param_name] = Annotated[python_type, param_desc]
            params.append(param_name)

        # Create the dynamic async function that accepts both positional and keyword args
        async def dynamic_tool_func(self, *args, **kwargs):
            """Dynamically generated function that calls MCP tool"""
            # Map positional args to parameter names
            for i, arg_value in enumerate(args):
                if i < len(params):
                    kwargs[params[i]] = arg_value

            # Auto-inject reg parameter if tool needs it
            if "reg" in tool_schema.get("properties", {}):
                kwargs["reg"] = self.car.reg

            # Convert date objects to ISO strings for MCP
            for key, value in list(kwargs.items()):
                if isinstance(value, date):
                    kwargs[key] = value.isoformat()

            logger.info(f"[MCP CALL] {tool_name}({kwargs})")
            return await self._call_mcp_tool(tool_name, kwargs)

        # Set function metadata
        dynamic_tool_func.__name__ = tool_name
        dynamic_tool_func.__doc__ = tool_description

        # Build proper signature with annotations
        sig_params = [inspect.Parameter('self', inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        for param_name in params:
            sig_params.append(
                inspect.Parameter(
                    param_name,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=annotations[param_name]
                )
            )
        dynamic_tool_func.__signature__ = inspect.Signature(sig_params)
        dynamic_tool_func.__annotations__ = annotations

        # Apply the @function_tool decorator
        decorated_func = function_tool(dynamic_tool_func)

        # Bind to this instance
        bound_method = decorated_func.__get__(self, self.__class__)
        setattr(self, tool_name, bound_method)

    async def _get_mcp_session(self) -> ClientSession:
        """Get or create MCP session for runtime calls"""
        if self._mcp_session is None:
            stdio_transport = stdio_client(self._server_params)
            stdio, write = await stdio_transport.__aenter__()
            session = ClientSession(stdio, write)
            await session.__aenter__()
            await session.initialize()

            self._mcp_session = session
            self._stdio_transport = stdio_transport
            logger.info("🔌 MCP runtime session established")

        return self._mcp_session

    async def _call_mcp_tool(self, tool_name: str, arguments: dict[str, Any]) -> str:
        """Call an MCP tool and return the result"""
        try:
            session = await self._get_mcp_session()
            result = await session.call_tool(tool_name, arguments)

            # Extract text from result
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return "No response from MCP server"

        except Exception as e:
            logger.error(f"❌ MCP tool call failed: {e}")
            return f"Error calling booking service: {e}"

    def get_car_str(self):
        """Get car details as formatted string"""
        car_str = ""
        for field, value in asdict(self.car).items():
            car_str += f"{field}: {value}\n"
        return car_str

    async def on_enter(self) -> None:
        """Called when agent becomes active - check existing booking"""
        try:
            # Get existing booking via dynamically discovered MCP tool
            result = await self._call_mcp_tool("get_booking", {"reg": self.car.reg})

            car_details = f"""Registration: {self.car.reg},
                            Make: {self.car.make},
                            Model: {self.car.model},
                            Year: {self.car.year}"""

            if "No appointment found" in result:
                # Get next available date
                today_iso = date.today().isoformat()
                next_date_result = await self._call_mcp_tool(
                    "get_next_available_booking_date",
                    {"reg": self.car.reg, "earliest_date": today_iso}
                )

                await self.session.generate_reply(
                    instructions=f"""Always speak English unless the customer speaks another language or asks you to use another language.
                    Tell the customer you have the following details of their car: {car_details}.
                    Tell them they have no existing bookings, {next_date_result.replace('The next available booking date is', 'the next available booking date is')}, and ask if they would like to make one."""
                )
            else:
                # Has existing booking
                await self.session.generate_reply(
                    instructions=f"""Always speak English unless the customer speaks another language or asks you to use another language.
                    Tell the customer you have the following details of their car: {car_details}.
                    {result}"""
                )
        except Exception as e:
            logger.error(f"Error in on_enter: {e}")
            await self.session.generate_reply(
                instructions=f"""Always speak English unless the customer speaks another language or asks you to use another language.
                Tell the customer you have their car details but are having trouble checking bookings right now."""
            )

    @function_tool
    async def get_car_details(self):
        """
        Get details of the customer's car.
        NOTE: This is the ONLY explicitly defined tool - all booking tools are dynamically discovered!
        """
        logger.info("get car details (explicit tool)")
        return f"The car details are: {self.get_car_str()}"
