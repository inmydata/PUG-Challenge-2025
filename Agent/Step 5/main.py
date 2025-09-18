from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession
from prompts import WELCOME_MESSAGE
from agent import Assistant
from livekit.plugins import (
    openai
)

load_dotenv(".env", override=True)

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="shimmer",
            temperature=0.8
        )
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=WELCOME_MESSAGE
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))