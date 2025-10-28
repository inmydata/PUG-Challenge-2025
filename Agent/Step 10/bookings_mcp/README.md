# MCP Server Integration - Model Context Protocol

## What is MCP?

**Model Context Protocol (MCP)** is an open protocol that enables AI applications to securely connect to external data sources and tools. Think of it as a standardized way for AI agents to discover and use external capabilities without hard-coding them.

In simple terms: Instead of writing code that says "I have these 5 specific tools," MCP lets you ask "What tools are available?" and automatically use whatever you discover.

## Why MCP Matters

### The Old Way (Hard-Coded Tools)

```python
class BookingAssistant:
    @function_tool
    async def book_appointment(self, date, description):
        # Hard-coded implementation
        result = driver.save_booking(self.car.reg, date, description)
        return result

    @function_tool
    async def get_booking(self):
        # Hard-coded implementation
        booking = driver.get_booking(self.car.reg)
        return booking

    # Every tool must be explicitly defined!
```

**Problems:**
- ❌ Every tool is hard-coded
- ❌ Adding a new tool requires changing agent code
- ❌ Can't share tools between different agents easily
- ❌ Tight coupling between agent and business logic

### The MCP Way (Dynamic Discovery)

```python
class BookingAssistant:
    def __init__(self, car):
        # Connect to MCP server
        # Discover what tools it has
        # Automatically create function_tool methods
        # NO HARD-CODED TOOLS!

    # Only ONE explicitly defined tool:
    @function_tool
    async def get_car_details(self):
        return self.car
```

**Benefits:**
- ✅ Tools discovered automatically at runtime
- ✅ Add new tools by just updating the MCP server
- ✅ Multiple agents can use the same MCP server
- ✅ Loose coupling - agent doesn't know about business logic
- ✅ MCP servers can be written in any language
- ✅ Tools can be swapped, versioned, and tested independently

## How It Works in This Project

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenEdge Autos Agent                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────────┐         ┌────────────────────┐      │
│  │  AccountAssistant  │────────>│  OEDatabaseDriver  │      │
│  │  (Car Lookup)      │         │  (Direct Calls)    │      │
│  └────────────────────┘         └────────────────────┘      │
│           │                                                 │
│           │ Transfers to                                    │
│           ▼                                                 │
│  ┌────────────────────┐                                     │
│  │ BookingAssistant   │                                     │
│  │ (Booking Mgmt)     │                                     │
│  └─────────┬──────────┘                                     │
│            │                                                │
│            │ stdio (stdin/stdout)                           │
│            │                                                │
└────────────┼────────────────────────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────────────┐
│           MCP Server (Separate Process)                    │
│           bookings_mcp/server.py                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Available Tools:                                          │
│  • get_the_date_today()                                    │
│  • get_next_available_booking_date(reg, earliest_date)     │
│  • book_appointment(reg, date, description)                │
│  • get_booking(reg)                                        │
│                                                            │
│  Each tool makes HTTP calls to backend API                 │
│                                                            │
└────────────┬───────────────────────────────────────────────┘
             │ HTTP
             ▼
┌────────────────────────────────────────────────────────────┐
│              Backend API (OpenEdge Service)                │
│              (Car & Booking Database)                      │
└────────────────────────────────────────────────────────────┘
```

### The Magic: Dynamic Tool Discovery

When `BookingAssistant` is initialized, here's what happens:

#### Step 1: Setup (Before Agent Starts)

```python
def __init__(self, car: Car):
    self.car = car

    # CRITICAL: Discover tools BEFORE calling super().__init__()
    self._setup_dynamic_tools()  # ← The magic happens here!

    super().__init__(...)  # LiveKit initialization
```

#### Step 2: Connect to MCP Server

```python
def _setup_dynamic_tools(self):
    # 1. Set parameters for launching MCP server subprocess
    server_params = StdioServerParameters(
        command=sys.executable,                      # Python
        args=["bookings_mcp/server.py"],            # Server script
        env={**os.environ}
    )

    # 2. Launch subprocess and connect
    tools = await self._discover_mcp_tools()
```

#### Step 3: Ask "What Tools Do You Have?"

```python
async def _discover_mcp_tools(self):
    # Connect via stdio
    stdio_transport = stdio_client(self._server_params)
    session = ClientSession(stdio, write)
    await session.initialize()

    # Ask the server: "What tools do you provide?"
    tools_result = await session.list_tools()

    # Returns something like:
    # [
    #   Tool(name="book_appointment", description="...", inputSchema={...}),
    #   Tool(name="get_booking", description="...", inputSchema={...}),
    #   ...
    # ]

    return tools_result.tools
```

#### Step 4: Dynamically Create Python Methods

```python
def _create_dynamic_tool(self, mcp_tool):
    tool_name = mcp_tool.name
    tool_schema = mcp_tool.inputSchema

    # Parse the schema to understand parameters
    properties = tool_schema.get("properties", {})

    # Create a Python async function dynamically
    async def dynamic_tool_func(self, *args, **kwargs):
        # Auto-inject car registration
        kwargs["reg"] = self.car.reg

        # Convert dates to ISO format
        # ... parameter processing ...

        # Call the MCP server
        return await self._call_mcp_tool(tool_name, kwargs)

    # Set proper function metadata
    dynamic_tool_func.__name__ = tool_name
    dynamic_tool_func.__doc__ = tool_schema.description

    # Apply LiveKit's @function_tool decorator programmatically
    decorated_func = function_tool(dynamic_tool_func)

    # Attach to this instance
    setattr(self, tool_name, decorated_func)
```

**Result:** The agent now has methods like `self.book_appointment()`, `self.get_booking()`, etc., but **they were never hard-coded!**

#### Step 5: Runtime - Calling Tools

When the LLM decides to call a tool:

```python
# LLM says: "Call book_appointment with date='2025-11-04', description='Oil change'"

# LiveKit calls our dynamically created method:
await agent.book_appointment(date="2025-11-04", description="Oil change")

# Our dynamic function:
async def dynamic_tool_func(self, *args, **kwargs):
    kwargs["reg"] = self.car.reg  # Auto-inject: "ABC123"
    # kwargs now: {"date": "2025-11-04", "description": "Oil change", "reg": "ABC123"}

    return await self._call_mcp_tool("book_appointment", kwargs)

# _call_mcp_tool sends to MCP server via stdio:
async def _call_mcp_tool(self, tool_name, arguments):
    session = await self._get_mcp_session()
    result = await session.call_tool(tool_name, arguments)
    return result.content[0].text

# MCP server executes and returns result
```

## The MCP Server (bookings_mcp/server.py)

The MCP server is a standalone Python script using the `mcp` library:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("bookings-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Tell clients what tools are available"""
    return [
        Tool(
            name="book_appointment",
            description="Book an appointment",
            inputSchema={
                "type": "object",
                "properties": {
                    "reg": {"type": "string", "description": "Car registration"},
                    "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                    "description": {"type": "string", "description": "Purpose"}
                },
                "required": ["reg", "date", "description"]
            }
        ),
        # ... other tools ...
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Execute the requested tool"""
    if name == "book_appointment":
        # Make HTTP call to backend API
        response = requests.post(f"{BASE_URL}/booking", json={
            "reg": arguments["reg"],
            "date": arguments["date"],
            "description": arguments["description"]
        })
        return [TextContent(type="text", text=f"Booked: {response.text}")]
```

The server runs as a **separate subprocess** and communicates via stdin/stdout.

## Why This Is Powerful

### 1. **Zero-Code Tool Addition**

Want to add a `cancel_booking` tool?

**Old way:**
```python
# Edit bookingAgent.py
@function_tool
async def cancel_booking(self, reason: str):
    # Write implementation
    # Update imports
    # Test integration
    # Deploy new agent code
```

**MCP way:**
```python
# Edit bookings_mcp/server.py ONLY
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # ... existing code ...

    elif name == "cancel_booking":  # ← Add this
        # Implementation
        return [TextContent(type="text", text="Cancelled")]

# Add to list_tools():
Tool(name="cancel_booking", description="Cancel a booking", ...)
```

**That's it!** Restart the agent and `cancel_booking` is automatically available. No agent code changes.

### 2. **Tool Reusability**

The same MCP server can be used by multiple agents:

```python
# Different agents, same MCP server
class BookingAssistant(Agent):
    # Uses bookings_mcp server

class CustomerServiceAgent(Agent):
    # ALSO uses bookings_mcp server

class ReportingAgent(Agent):
    # ALSO uses bookings_mcp server
```

### 3. **Language Agnostic**

MCP servers can be written in **any language**:
- Python (FastMCP)
- TypeScript/JavaScript
- Rust
- Go

As long as they speak the MCP protocol, your Python agent can use them.

### 4. **Independent Development**

- **Backend team** can update booking logic in the MCP server
- **Agent team** doesn't need to change anything
- **Testing** can happen independently
- **Versioning** is cleaner

### 5. **Security & Isolation**

The MCP server:
- Runs in a separate process
- Can have its own permissions
- Can be sandboxed
- Handles sensitive API keys separate from agent code

## Comparison: With vs Without MCP

| Aspect | Without MCP | With MCP |
|--------|-------------|----------|
| **Adding a tool** | Edit agent code, redeploy | Edit MCP server only |
| **Tool discovery** | Hard-coded list | Automatic at runtime |
| **Sharing tools** | Copy-paste code | Point to same server |
| **Testing tools** | Test entire agent | Test MCP server independently |
| **Technology** | Must be Python | Any language |
| **Coupling** | Tight (agent knows everything) | Loose (agent discovers) |
| **Agent complexity** | High (business logic + AI) | Low (just AI orchestration) |

## Real-World Use Case

Imagine you're building an AI customer service system:

### Without MCP
```
┌─────────────────────────────────────┐
│   Monolithic Agent                  │
│                                     │
│   - Calendar management code        │
│   - Email sending code              │
│   - Database queries                │
│   - Payment processing              │
│   - SMS notifications               │
│   - Report generation               │
│   - All business logic              │
│                                     │
│   (1 huge file, 5000+ lines)        │
└─────────────────────────────────────┘
```

### With MCP
```
┌──────────────────────┐
│   Lightweight Agent  │
│   (AI orchestration  │
│    only, ~200 lines) │
└──────────┬───────────┘
           │
           ├──────▶ Calendar MCP Server
           ├──────▶ Email MCP Server
           ├──────▶ Database MCP Server
           ├──────▶ Payment MCP Server
           ├──────▶ SMS MCP Server
           └──────▶ Reports MCP Server
```

Each MCP server:
- Developed by different teams
- Written in optimal language
- Versioned independently
- Tested separately
- Deployed separately

The agent just **discovers and orchestrates**.

## How to Add a New Tool

Let's add a `reschedule_booking` tool:

### Step 1: Update MCP Server

Edit `bookings_mcp/server.py`:

```python
# In list_tools():
@app.list_tools()
async def list_tools():
    return [
        # ... existing tools ...
        Tool(
            name="reschedule_booking",
            description="Reschedule an existing booking to a new date",
            inputSchema={
                "type": "object",
                "properties": {
                    "reg": {
                        "type": "string",
                        "description": "Car registration number"
                    },
                    "new_date": {
                        "type": "string",
                        "description": "New date in ISO format (YYYY-MM-DD)"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rescheduling"
                    }
                },
                "required": ["reg", "new_date", "reason"]
            }
        )
    ]

# In call_tool():
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # ... existing code ...

    elif name == "reschedule_booking":
        reg = arguments["reg"]
        new_date = arguments["new_date"]
        reason = arguments["reason"]

        # Call your backend API
        url = f"{BASE_URL}booking/reschedule"
        response = requests.post(url, json={
            "reg": reg,
            "newDate": new_date,
            "reason": reason
        })

        if response.status_code == 200:
            return [TextContent(
                type="text",
                text=f"Booking rescheduled to {new_date}. Reason: {reason}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to reschedule: {response.text}"
            )]
```

### Step 2: That's It!

**No changes to `bookingAgent.py` needed!**

Restart the agent, and when it initializes:
1. Connects to MCP server
2. Asks "What tools do you have?"
3. Gets back 5 tools (including the new `reschedule_booking`)
4. Dynamically creates methods for all 5
5. LLM can now call `reschedule_booking`

### Testing

```python
from bookingAgent import BookingAssistant
from OEDatabaseDriver import Car

car = Car(reg="ABC123", make="Audi", model="A4", year=2020)
agent = BookingAssistant(car=car)

# The new tool is automatically available!
result = await agent.reschedule_booking(
    new_date="2025-12-01",
    reason="Customer requested different time"
)
```

## Technical Deep Dive

### Parameter Mapping

The system intelligently maps MCP tool parameters:

```python
# MCP Tool Schema:
{
    "properties": {
        "reg": {"type": "string"},           # Auto-injected
        "earliest_date": {"type": "string"}  # Becomes Python param
    }
}

# Becomes Python function signature:
async def get_next_available_booking_date(
    self,
    earliest_date: Annotated[date, "Earliest date for booking"]
)

# When called:
agent.get_next_available_booking_date(earliest_date=date(2025, 11, 1))

# Auto-injects reg and converts date:
{
    "reg": "ABC123",                    # Injected
    "earliest_date": "2025-11-01"      # Converted from date object
}
```

### Type Conversion

```python
# JSON Schema → Python Type mapping:
"string" → str
"string" (with "date" in name/description) → date
"integer" → int
"number" → float

# Runtime conversion:
Python date → ISO string (YYYY-MM-DD)
Python str → str (unchanged)
```

### Communication Protocol

MCP uses JSON-RPC 2.0 over stdio:

```json
// Agent → MCP Server (list tools)
{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
}

// MCP Server → Agent (tool list)
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "tools": [
            {"name": "book_appointment", "description": "...", "inputSchema": {...}},
            ...
        ]
    }
}

// Agent → MCP Server (call tool)
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "book_appointment",
        "arguments": {"reg": "ABC123", "date": "2025-11-04", "description": "Service"}
    },
    "id": 2
}

// MCP Server → Agent (result)
{
    "jsonrpc": "2.0",
    "id": 2,
    "result": {
        "content": [
            {"type": "text", "text": "Appointment booked for 4th November 2025"}
        ]
    }
}
```

## Best Practices

### 1. Keep Agents Lightweight

Agents should orchestrate, not implement:

```python
# ❌ BAD: Agent has business logic
class BookingAssistant:
    async def book_appointment(self, date, desc):
        # Validate date
        # Check availability
        # Update database
        # Send confirmation email
        # Log to analytics
        # ... 100 lines of code

# ✅ GOOD: Agent just orchestrates
class BookingAssistant:
    # Discovers tools from MCP
    # Calls them when LLM decides
    # Returns results to user
```

### 2. Design for Discovery

MCP tools should be self-describing:

```python
# ✅ GOOD: Clear description
Tool(
    name="book_appointment",
    description="Book an appointment for a specific date. Use this when the customer wants to schedule a service.",
    inputSchema={...}
)

# ❌ BAD: Vague description
Tool(
    name="book_appointment",
    description="Books stuff",
    inputSchema={...}
)
```

### 3. Handle Errors Gracefully

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "book_appointment":
            response = requests.post(...)
            if response.status_code == 200:
                return [TextContent(type="text", text="Success")]
            else:
                return [TextContent(type="text", text=f"Failed: {response.text}")]
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
```

### 4. Version Your MCP Servers

```python
app = Server("bookings-server-v2")  # Version in name

# Or use different servers for different versions
if use_v2:
    server_path = "bookings_mcp_v2/server.py"
else:
    server_path = "bookings_mcp/server.py"
```

## Conclusion

MCP transforms how AI agents interact with tools:

- **Before MCP**: Hard-code every capability into the agent
- **With MCP**: Agents discover capabilities dynamically

This project demonstrates the full power of MCP by:
1. ✅ **Dynamic discovery** - No hard-coded booking tools
2. ✅ **Runtime injection** - Python methods created on-the-fly
3. ✅ **Clean separation** - Agent (AI) vs MCP Server (Business Logic)
4. ✅ **Extensibility** - Add tools without touching agent code

The result: **A flexible, maintainable, and powerful AI agent architecture.**

---

**Further Reading:**
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Anthropic MCP Introduction](https://www.anthropic.com/news/model-context-protocol)
