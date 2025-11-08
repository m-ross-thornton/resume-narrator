"""
Configuration settings for the Resume Narrator agent
"""
import os

# LLM Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# MCP Server URLs
MCP_RESUME_URL = os.getenv("MCP_RESUME_URL", "http://localhost:9001")
MCP_VECTOR_URL = os.getenv("MCP_VECTOR_URL", "http://localhost:9002")
MCP_CODE_URL = os.getenv("MCP_CODE_URL", "http://localhost:9003")

# Agent Configuration
SUBJECT_NAME = os.getenv("SUBJECT_NAME", "Ross")
MAX_AGENT_ITERATIONS = 10

# Chainlit Configuration
CHAINLIT_PORT = int(os.getenv("CHAINLIT_PORT", "8000"))
