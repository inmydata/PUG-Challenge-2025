from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession
from prompts import WELCOME_MESSAGE
from accountAgent import AccountAssistant
from OEDatabaseDriver import Car
from livekit.plugins import (
    openai
)

load_dotenv(".env", override=True)

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession[Car](
        llm=openai.realtime.RealtimeModel(
            voice="shimmer",
            temperature=0.8
        )
    )

    await session.start(
        room=ctx.room,
        agent=AccountAssistant()
    )

    await ctx.connect()

    await session.generate_reply(
        instructions=WELCOME_MESSAGE
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))