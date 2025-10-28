#!/usr/bin/env python3
"""
Bookings MCP Server
Provides booking management tools via MCP protocol
"""

import os
from datetime import datetime, date
from typing import Optional
import requests
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Load environment variables
load_dotenv(override=True)

BASE_URL = os.getenv("OE_SERVICE_URL")

# Initialize MCP server
app = Server("bookings-server")


def date_to_long_string(d: date) -> str:
    """Convert date to UK format with ordinal suffix"""
    day = d.day
    # Work out suffix
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix} {d.strftime('%B %Y')}"


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available booking tools"""
    return [
        Tool(
            name="get_the_date_today",
            description="Get today's date in a formatted string",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_next_available_booking_date",
            description="Get the next available booking date from a given start date",
            inputSchema={
                "type": "object",
                "properties": {
                    "reg": {
                        "type": "string",
                        "description": "Car registration number"
                    },
                    "earliest_date": {
                        "type": "string",
                        "description": "Earliest date for booking in ISO format (YYYY-MM-DD)"
                    }
                },
                "required": ["reg", "earliest_date"]
            }
        ),
        Tool(
            name="book_appointment",
            description="Book an appointment for a specific date",
            inputSchema={
                "type": "object",
                "properties": {
                    "reg": {
                        "type": "string",
                        "description": "Car registration number"
                    },
                    "date": {
                        "type": "string",
                        "description": "Date for the appointment in ISO format (YYYY-MM-DD)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the appointment"
                    }
                },
                "required": ["reg", "date", "description"]
            }
        ),
        Tool(
            name="get_booking",
            description="Get the existing booking for a car registration",
            inputSchema={
                "type": "object",
                "properties": {
                    "reg": {
                        "type": "string",
                        "description": "Car registration number"
                    }
                },
                "required": ["reg"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""

    if name == "get_the_date_today":
        date_str = date_to_long_string(date.today())
        return [TextContent(
            type="text",
            text=f"The date today is {date_str}"
        )]

    elif name == "get_next_available_booking_date":
        reg = arguments["reg"]
        earliest_date_str = arguments["earliest_date"]

        # Parse ISO date
        try:
            earliest_date = datetime.fromisoformat(earliest_date_str).date()
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Invalid date format: {e}"
            )]

        # Call API
        url = f"{BASE_URL}booking/next"
        formatted_date = earliest_date.strftime("%d-%m-%Y")

        try:
            r = requests.get(
                url,
                params={"startDate": formatted_date},
                headers={"Accept": "application/json"},
                timeout=10
            )

            if r.status_code == 200:
                data = r.json()
                bd = data.get("BookingDate")
                if bd:
                    next_date = datetime.strptime(bd, "%d-%m-%Y").date()
                    date_str = date_to_long_string(next_date)
                    return [TextContent(
                        type="text",
                        text=f"The next available booking date is {date_str}"
                    )]
                else:
                    return [TextContent(type="text", text="No booking date available")]
            elif r.status_code in (204, 404):
                return [TextContent(type="text", text="No booking date available")]
            else:
                return [TextContent(
                    type="text",
                    text=f"Unexpected status {r.status_code}: {r.text}"
                )]

        except requests.RequestException as e:
            return [TextContent(type="text", text=f"Request failed: {e}")]

    elif name == "book_appointment":
        reg = arguments["reg"].upper().replace(" ", "")
        date_str = arguments["date"]
        description = arguments["description"]

        # Parse ISO date
        try:
            booking_date = datetime.fromisoformat(date_str).date()
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Invalid date format: {e}"
            )]

        # Call API
        url = f"{BASE_URL}booking"
        payload = {
            "reg": reg,
            "date": booking_date.strftime("%d-%m-%Y"),
            "description": description,
        }

        try:
            r = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if r.status_code == 200 and r.text.strip().upper() == "OK":
                formatted_date = date_to_long_string(booking_date)
                return [TextContent(
                    type="text",
                    text=f"Appointment booked for {formatted_date} with description: {description}"
                )]
            elif r.status_code == 409:
                return [TextContent(
                    type="text",
                    text=f"Conflict: {r.text.strip()}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to book appointment: {r.text}"
                )]

        except requests.RequestException as e:
            return [TextContent(type="text", text=f"Request failed: {e}")]

    elif name == "get_booking":
        reg = arguments["reg"].upper().replace(" ", "")

        # Call API
        url = f"{BASE_URL}booking/getbooking"

        try:
            r = requests.get(
                url,
                params={"reg": reg},
                headers={"Accept": "application/json"},
                timeout=10
            )

            if r.status_code == 200:
                data = r.json()
                bd = data.get("BookingDate")
                desc = data.get("Description", "")

                if bd:
                    booking_date = datetime.strptime(bd, "%d-%m-%Y").date()
                    formatted_date = date_to_long_string(booking_date)
                    return [TextContent(
                        type="text",
                        text=f"Next appointment is on {formatted_date} with description: {desc}"
                    )]
                else:
                    return [TextContent(type="text", text="No appointment found")]

            elif r.status_code in (204, 404):
                return [TextContent(type="text", text="No appointment found")]
            else:
                return [TextContent(
                    type="text",
                    text=f"Unexpected status {r.status_code}: {r.text}"
                )]

        except requests.RequestException as e:
            return [TextContent(type="text", text=f"Request failed: {e}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
