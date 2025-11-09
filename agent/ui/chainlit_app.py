# agent/ui/chainlit_app.py
import chainlit as cl
from agent.main import create_agent
import os

SUBJECT_NAME = os.getenv("SUBJECT_NAME", "Ross")


@cl.on_chat_start
async def start():
    executor = create_agent()
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

    # Update message content and persist
    msg.content = response["output"]
    await msg.update()
