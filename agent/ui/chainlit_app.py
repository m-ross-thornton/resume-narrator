# agent/ui/chainlit_app.py
"""
Chainlit UI for Resume Narrator Agent with streaming support.
Uses LangChain v1 astream_events() for real-time response streaming and tool tracking.
"""
import chainlit as cl
from agent.main import create_lc_agent
from agent.config import SUBJECT_NAME
import json
import logging

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    """Initialize the agent and welcome message on chat start."""
    agent = create_lc_agent()
    cl.user_session.set("agent", agent)

    await cl.Message(
        content="👋 Hello! I'm a resume narrator AI assistant. I can help you with:\n"
        f"• Generating a PDF of {SUBJECT_NAME}'s resume\n"
        "• Answering questions about your experience\n"
        "• Explaining how I work internally"
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Stream agent responses with tool call tracking using LangChain v1 astream_events.
    Implements the fix from https://github.com/Chainlit/chainlit/issues/2607
    """
    agent = cl.user_session.get("agent")

    # Create message container for streaming response
    msg = cl.Message(content="")
    await msg.send()

    # Track tool calls with steps
    steps_dict = {}

    try:
        # Check if agent supports astream_events (LangChain v1.x feature)
        if hasattr(agent, "astream_events"):
            await _stream_with_events(agent, message, msg, steps_dict)
        else:
            # Fallback to invoke for older LangChain versions
            logger.info("astream_events not available, using invoke fallback")
            await _invoke_without_streaming(agent, message, msg)

        # Final update to ensure message is persisted
        if not msg.content:
            msg.content = (
                "I processed your request but received no response. Please try again."
            )
            await msg.update()

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        msg.content = f"An error occurred: {str(e)}"
        await msg.update()


async def _stream_with_events(agent, message, msg, steps_dict):
    """
    Stream response using astream_events for real-time updates.

    Handles:
    - Tool start/end/error events with Chainlit Step visualization
    - Chat model streaming for progressive content display
    - Chain execution completion
    """
    try:
        async for event in agent.astream_events(
            {"input": message.content}, version="v2"
        ):
            kind = event.get("event")
            run_id = event.get("run_id")

            # Handle tool calls starting
            if kind == "on_tool_start":
                data = event.get("data", {})
                tool_name = data.get("tool_name")
                tool_input = data.get("input")

                if tool_name:
                    # Create a step for tool execution visualization
                    step = cl.Step(
                        name=f"Tool: {tool_name}",
                        type="tool",
                    )
                    step.input = (
                        json.dumps(tool_input, indent=2)
                        if isinstance(tool_input, dict)
                        else str(tool_input)
                    )
                    await step.send()
                    steps_dict[run_id] = step
                    logger.debug(f"Started tool execution: {tool_name}")

            # Handle tool completion
            elif kind == "on_tool_end":
                data = event.get("data", {})
                output = data.get("output")

                if run_id in steps_dict:
                    step = steps_dict[run_id]
                    step.output = (
                        json.dumps(output, indent=2)
                        if not isinstance(output, str)
                        else output
                    )
                    step.status = "done"
                    await step.update()
                    logger.debug(f"Tool execution completed: {step.name}")

            # Handle tool errors
            elif kind == "on_tool_error":
                data = event.get("data", {})
                error = data.get("error")

                if run_id in steps_dict:
                    step = steps_dict[run_id]
                    step.output = f"Error: {error}"
                    step.status = "error"
                    await step.update()
                    logger.error(f"Tool error in {step.name}: {error}")

            # Stream model output chunks for progressive display
            elif kind == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")

                if chunk and hasattr(chunk, "content") and chunk.content:
                    # Append streamed content to message for real-time display
                    msg.content += chunk.content
                    await msg.update()
                    logger.debug(f"Streamed {len(chunk.content)} characters")

            # Handle chain execution completion
            elif kind == "on_chain_end":
                data = event.get("data", {})
                output = data.get("output")

                # Extract final response content
                if output and isinstance(output, dict):
                    final_content = _extract_output(output)
                    if final_content:
                        msg.content = final_content
                        await msg.update()

    except Exception as e:
        logger.warning(f"Streaming with events failed: {e}")
        # Fallback to non-streaming invoke
        await _invoke_without_streaming(agent, message, msg)


async def _invoke_without_streaming(agent, message, msg):
    """
    Fallback method for agents that don't support astream_events.
    Uses synchronous invoke wrapped in async.
    """
    logger.info("Using fallback invoke method (non-streaming)")

    try:
        # Run agent invoke asynchronously
        response = await cl.make_async(agent.invoke)({"input": message.content})

        # Extract the final response
        if response:
            final_content = _extract_output(response)
            msg.content = final_content or "No response received from agent."
        else:
            msg.content = "No response received from agent."

        await msg.update()

    except Exception as e:
        logger.error(f"Error in fallback invoke: {str(e)}", exc_info=True)
        msg.content = f"Error processing request: {str(e)}"
        await msg.update()


def _extract_output(response):
    """
    Extract the final response content from various agent output formats.

    Handles:
    - Direct string output
    - Messages array with content
    - Dict with 'output' key
    - Various response structures
    """
    if isinstance(response, str):
        return response

    if not isinstance(response, dict):
        return str(response)

    # Try different extraction methods
    if "output" in response and isinstance(response["output"], str):
        return response["output"]

    if "messages" in response and response["messages"]:
        try:
            last_message = response["messages"][-1]
            if hasattr(last_message, "content"):
                return last_message.content
            elif isinstance(last_message, dict) and "content" in last_message:
                return last_message["content"]
        except (IndexError, AttributeError, TypeError):
            pass

    if "result" in response:
        return str(response["result"])

    # Fallback: return the response as string
    return str(response)
