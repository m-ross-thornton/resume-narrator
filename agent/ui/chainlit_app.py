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
    logger.info("Chat session started, initializing agent...")
    try:
        agent = create_lc_agent()
        logger.info(f"Agent created successfully, type: {type(agent)}")
        cl.user_session.set("agent", agent)
        logger.info("Agent stored in user session")

        await cl.Message(
            content="👋 Hello! I'm a resume narrator AI assistant. I can help you with:\n"
            f"• Generating a PDF of {SUBJECT_NAME}'s resume\n"
            "• Answering questions about your experience\n"
            "• Explaining how I work internally"
        ).send()
        logger.info("Welcome message sent")
    except Exception as e:
        logger.error(f"Error during chat start: {e}", exc_info=True)
        await cl.Message(content=f"Error initializing agent: {str(e)}").send()


@cl.on_message
async def main(message: cl.Message):
    """
    Stream agent responses with tool call tracking using LangChain v1 astream_events.
    Implements the fix from https://github.com/Chainlit/chainlit/issues/2607
    """
    logger.info(f"Processing user message: {message.content[:100]}...")
    agent = cl.user_session.get("agent")

    if not agent:
        logger.error("Agent not found in user session!")
        await cl.Message(content="Error: Agent not initialized").send()
        return

    # Create message container for streaming response
    msg = cl.Message(content="")
    await msg.send()

    # Track tool calls with steps
    steps_dict = {}

    try:
        # Check if agent supports astream_events (LangChain v1.x feature)
        logger.debug(f"Agent has astream_events: {hasattr(agent, 'astream_events')}")
        logger.debug(f"Agent type: {type(agent)}")

        if hasattr(agent, "astream_events"):
            logger.info("Using astream_events for streaming response")
            await _stream_with_events(agent, message, msg, steps_dict)
        else:
            # Fallback to invoke for older LangChain versions
            logger.info("astream_events not available, using invoke fallback")
            await _invoke_without_streaming(agent, message, msg)

        # Final check and update to ensure message is persisted
        logger.debug(f"Message content after processing: {len(msg.content)} chars")
        logger.debug(f"Message content (first 100 chars): {msg.content[:100]}")

        if not msg.content:
            logger.warning(
                "No content in message after processing, using fallback message"
            )
            msg.content = (
                "I processed your request but received no response. Please try again."
            )
            await msg.update()
        else:
            logger.info(
                f"Successfully processed message with {len(msg.content)} characters"
            )

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
        logger.info("Starting event streaming with astream_events...")
        event_count = 0
        stream_event_count = 0
        chain_end_count = 0

        async for event in agent.astream_events(
            {"input": message.content}, version="v2"
        ):
            event_count += 1
            kind = event.get("event")
            run_id = event.get("run_id")

            if kind == "on_chat_model_stream":
                stream_event_count += 1
            elif kind == "on_chain_end":
                chain_end_count += 1

            logger.debug(f"Event #{event_count}: type={kind}, run_id={run_id}")

            # Handle tool calls starting
            if kind == "on_tool_start":
                data = event.get("data", {})
                tool_name = data.get("tool_name")
                tool_input = data.get("input")

                logger.info(f"Tool starting: {tool_name}")
                logger.debug(f"Tool input: {tool_input}")

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
                    logger.info(f"Started tool execution: {tool_name}")

            # Handle tool completion
            elif kind == "on_tool_end":
                data = event.get("data", {})
                output = data.get("output")

                logger.info(f"Tool ended, output type: {type(output)}")
                logger.debug(f"Tool output: {str(output)[:200]}")

                if run_id in steps_dict:
                    step = steps_dict[run_id]
                    step.output = (
                        json.dumps(output, indent=2)
                        if not isinstance(output, str)
                        else output
                    )
                    step.status = "done"
                    await step.update()
                    logger.info(f"Tool execution completed: {step.name}")
                else:
                    logger.warning(
                        f"Received on_tool_end but no step found for run_id {run_id}"
                    )

            # Handle tool errors
            elif kind == "on_tool_error":
                data = event.get("data", {})
                error = data.get("error")

                logger.error(f"Tool error occurred: {error}")

                if run_id in steps_dict:
                    step = steps_dict[run_id]
                    step.output = f"Error: {error}"
                    step.status = "error"
                    await step.update()
                    logger.error(f"Tool error in {step.name}: {error}")
                else:
                    logger.warning(
                        f"Received on_tool_error but no step found for run_id {run_id}"
                    )

            # Stream model output chunks for progressive display
            elif kind == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")

                logger.debug(f"Chat model stream event, chunk type: {type(chunk)}")

                # Log chunk details
                if chunk:
                    if hasattr(chunk, "content"):
                        logger.debug(
                            f"Chunk has content attribute: '{chunk.content}' (len={len(chunk.content) if chunk.content else 0})"
                        )
                    if hasattr(chunk, "__dict__"):
                        logger.debug(f"Chunk attributes: {chunk.__dict__}")

                if chunk and hasattr(chunk, "content") and chunk.content:
                    # Append streamed content to message for real-time display
                    msg.content += chunk.content
                    await msg.update()
                    logger.debug(f"Streamed {len(chunk.content)} characters")
                else:
                    logger.debug(f"Skipped empty chunk (chunk={chunk})")

            # Handle chain execution completion
            elif kind == "on_chain_end":
                data = event.get("data", {})
                output = data.get("output")

                logger.info(f"Chain ended, output type: {type(output)}")

                # Log FULL response structure for debugging (not truncated!)
                if isinstance(output, dict):
                    logger.info(f"Chain output keys: {list(output.keys())}")
                    # Log the ENTIRE output dict
                    logger.info(f"Full chain output dict: {output}")

                    # Log messages if present
                    if "messages" in output:
                        msgs = output["messages"]
                        logger.info(f"Number of messages: {len(msgs)}")
                        for i, msg_item in enumerate(msgs):
                            logger.info(f"  Message {i} type: {type(msg_item)}")
                            if hasattr(msg_item, "__dict__"):
                                logger.info(f"    Attributes: {msg_item.__dict__}")
                            elif isinstance(msg_item, dict):
                                logger.info(f"    Content: {msg_item}")
                            else:
                                logger.info(f"    Repr: {repr(msg_item)}")
                else:
                    logger.info(f"Chain output (full): {output}")

                # Extract final response content
                if output and isinstance(output, dict):
                    final_content = _extract_output(output)
                    logger.info(
                        f"Extracted content: {final_content[:100] if final_content else 'None'}"
                    )
                    if final_content:
                        msg.content = final_content
                        await msg.update()
                else:
                    logger.debug(
                        f"Skipping chain_end processing, output type not dict: {type(output)}"
                    )
            else:
                logger.debug(f"Ignoring event type: {kind}")

        logger.info(
            f"Event streaming completed: {event_count} total events, "
            f"{stream_event_count} stream events, {chain_end_count} chain_end events. "
            f"Final message content length: {len(msg.content)} chars"
        )

    except Exception as e:
        logger.warning(f"Streaming with events failed: {e}", exc_info=True)
        logger.info("Falling back to non-streaming invoke")
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
        logger.debug(f"Calling agent.invoke with message: {message.content[:100]}...")
        response = await cl.make_async(agent.invoke)({"input": message.content})

        logger.info(f"Agent.invoke returned, response type: {type(response)}")
        logger.debug(f"Response structure: {str(response)[:500]}")

        # Extract the final response
        if response:
            logger.info("Response received, extracting output...")
            final_content = _extract_output(response)
            logger.info(f"Extracted content type: {type(final_content)}")
            logger.debug(
                f"Extracted content: {final_content[:200] if final_content else 'None'}"
            )

            msg.content = final_content or "No response received from agent."
            logger.info(f"Message content set to {len(msg.content)} characters")
        else:
            logger.warning("Response was None or empty")
            msg.content = "No response received from agent."

        await msg.update()
        logger.info("Message updated in Chainlit UI")

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
    logger.debug(f"_extract_output called with response type: {type(response)}")

    if isinstance(response, str):
        logger.info(f"Response is string, returning directly ({len(response)} chars)")
        return response

    if not isinstance(response, dict):
        logger.debug(f"Response is not dict or string, converting to string")
        return str(response)

    logger.debug(f"Response is dict with keys: {response.keys()}")

    # Try different extraction methods
    if "output" in response and isinstance(response["output"], str):
        logger.info(f"Found 'output' key in response dict")
        return response["output"]

    if "messages" in response and response["messages"]:
        logger.info(f"Found 'messages' key with {len(response['messages'])} messages")
        try:
            last_message = response["messages"][-1]
            logger.debug(f"Last message type: {type(last_message)}")
            logger.debug(f"Last message: {last_message}")

            # Log message attributes if it's an object
            if hasattr(last_message, "__dict__"):
                logger.debug(f"Last message attributes: {last_message.__dict__}")

            if hasattr(last_message, "content"):
                logger.info(
                    f"Extracting content from message object, content='{last_message.content}'"
                )
                return last_message.content
            elif isinstance(last_message, dict) and "content" in last_message:
                logger.info(
                    f"Extracting content from message dict, content='{last_message['content']}'"
                )
                return last_message["content"]
            else:
                logger.warning(f"Last message has no content attribute or field")
                # Try to extract any text-like fields from the message
                if isinstance(last_message, dict):
                    logger.warning(f"Message dict keys: {list(last_message.keys())}")
                    # Try common alternative field names
                    for field in ["text", "response", "answer", "output"]:
                        if field in last_message:
                            logger.info(f"Found alternative field '{field}' in message")
                            return str(last_message[field])
        except (IndexError, AttributeError, TypeError) as e:
            logger.warning(f"Error extracting from messages: {e}", exc_info=True)
            pass

    if "result" in response:
        logger.info(f"Found 'result' key in response dict")
        return str(response["result"])

    # Fallback: return the response as string
    logger.warning(
        f"Could not extract output using standard methods, returning full response as string"
    )
    return str(response)
