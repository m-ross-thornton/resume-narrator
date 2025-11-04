# agent/ui/chainlit_app.py
import chainlit as cl
from agent.main import ResumeNarrator
import os

SUBJECT_NAME = os.getenv("SUBJECT_NAME", "Ross")


@cl.on_chat_start
async def start():
    agent = ResumeNarrator()
    executor = agent.create_agent()
    cl.user_session.set("agent", executor)

    await cl.Message(
        content="👋 Hello! I'm a resume narrator AI assistant. I can help you with:\n"
        f"• Generating a PDF of {SUBJECT_NAME}'s resume\n"
        "• Answering questions about your experience\n"
        "• Explaining how I work internally"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")

    # Process with thinking message
    msg = cl.Message(content="")
    await msg.send()

    # Stream response
    response = await cl.make_async(agent.invoke)({"input": message.content})

    await msg.update(content=response["output"])
