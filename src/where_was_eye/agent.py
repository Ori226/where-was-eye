"""
AI Agent Integration for Where Was Eye

This module provides agent classes that integrate with various AI providers
(OpenAI, Ollama) to answer questions about location history using the timeline database.
"""

from typing import Any, Dict, List, Optional, Union
import os
from dataclasses import dataclass
import json

from .timeline_db import MyTimelineDB

# Optional imports for different AI providers
try:
    from openai import OpenAI as OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from ollama import Client as OllamaClient
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class AgentConfig:
    """Configuration for the AI agent."""
    provider: str = "openai"  # "openai" or "ollama"
    model: str = "gpt-4.1"
    temperature: float = 0.0
    timeline_db_path: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_host: str = "http://localhost:11434"


class WhereWasEyeAgent:
    """
    Main agent class that uses AI to answer questions about location history.
    
    This class can work with either OpenAI or Ollama as the AI provider.
    """
    
    SYSTEM_PROMPT = """You are a helpful self archive/historian agent. You have access to a tool that can retrieve the geographical location (latitude and longitude) of a given city at a specified time by browsing through Google timeline. Use this tool to answer questions about where you were at a given time. If you don't know the answer, just say you don't know. Do not make up an answer.

In case the date or hours or minutes are not given, use the current date and time or use approximation like middle of the day or middle of the month.
When given the location, please try to give a location which is as exact as possible.
Instead of asking 'If you need a more precise address or further details, let me know' just share the precise address.
"""

    TOOLS = [
        {
            "type": "function",
            "function": {
                "name": "get_location_at_time",
                "description": "Retrieves the geographical location (latitude and longitude) at a specified time by browsing through Google timeline",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "year": {"type": "number", "description": "Year (e.g., 2024)"},
                        "month": {"type": "number", "description": "Month (1-12)"},
                        "day": {"type": "number", "description": "Day of month (1-31)"},
                        "hour": {"type": "number", "description": "Hour (0-23)"},
                        "minute": {"type": "number", "description": "Minute (0-59)"},
                    },
                    "required": ["year", "month", "day", "hour", "minute"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        }
    ]

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Agent configuration. If None, uses default values.
        """
        self.config = config or AgentConfig()
        self.timeline_db = None
        self._client = None
        
        self._initialize_timeline_db()
        self._initialize_ai_client()
        
    def _initialize_timeline_db(self):
        """Initialize the timeline database."""
        db_path = self.config.timeline_db_path
        if not db_path:
            # Use environment variable or default path
            db_path = os.environ.get("LOCATION_HISTORY_PATH")
            if not db_path:
                raise ValueError("Timeline database path not provided in config or environment")
        
        self.timeline_db = MyTimelineDB(db_path)
    
    def _initialize_ai_client(self):
        """Initialize the AI client based on provider."""
        if self.config.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI client not available. Install with: pip install openai")
            
            api_key = self.config.openai_api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided in config or environment")
            
            self._client = OpenAIClient(api_key=api_key)
            
        elif self.config.provider == "ollama":
            if not OLLAMA_AVAILABLE:
                raise ImportError("Ollama client not available. Install with: pip install ollama")
            
            self._client = OllamaClient(host=self.config.ollama_host)
            
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _run_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool function.
        
        Args:
            name: Tool name
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        if name == "get_location_at_time":
            # Ensure all arguments are integers
            for key in args:
                if not isinstance(args[key], int):
                    try:
                        args[key] = int(args[key])
                    except (ValueError, TypeError):
                        raise ValueError(f"Invalid value for {key}: {args[key]}")
            
            location = self.timeline_db.get_location_at_time(**args)
            return location
            
        raise ValueError(f"Unknown tool: {name}")
    
    def run(self, question: str) -> str:
        """
        Process a question about location history.
        
        Args:
            question: The question to answer (e.g., "Where was I on August 20, 2024 at 3:30 PM?")
            
        Returns:
            The AI's response with location information
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        
        if self.config.provider == "openai":
            return self._run_openai(messages)
        elif self.config.provider == "ollama":
            return self._run_ollama(messages)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def _run_openai(self, messages: List[Dict]) -> str:
        """Run the OpenAI-based agent."""
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=self.TOOLS,
            temperature=self.config.temperature,
        )
        
        message = response.choices[0].message
        
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            tool_result = self._run_tool(tool_name, tool_args)
            
            # Send result back to model
            final_response = self._client.chat.completions.create(
                model=self.config.model,
                messages=messages + [message] + [
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    }
                ],
                tools=self.TOOLS,
                temperature=self.config.temperature,
            )
            
            return final_response.choices[0].message.content
        else:
            return message.content
    
    def _run_ollama(self, messages: List[Dict]) -> str:
        """Run the Ollama-based agent."""
        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Ollama doesn't have system role, so we prepend to first user message
                if ollama_messages and ollama_messages[-1]["role"] == "user":
                    ollama_messages[-1]["content"] = msg["content"] + "\n\n" + ollama_messages[-1]["content"]
                else:
                    # If no user message yet, create one with system content
                    ollama_messages.append({"role": "user", "content": msg["content"]})
            else:
                ollama_messages.append(msg)
        
        response = self._client.chat(
            model=self.config.model,
            messages=ollama_messages,
            tools=self.TOOLS,
            options={"temperature": self.config.temperature},
        )
        
        if response.message.tool_calls:
            tool_call = response.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            
            tool_result = self._run_tool(tool_name, tool_args)
            
            final_response = self._client.chat(
                model=self.config.model,
                messages=ollama_messages + [response.message] + [
                    {"role": "tool", "content": str(tool_result)}
                ],
                tools=self.TOOLS,
                options={"temperature": self.config.temperature},
            )
            
            return final_response.message.content
        else:
            return response.message.content


# Simple factory function for convenience
def create_agent(
    provider: str = "openai",
    model: str = "gpt-4.1",
    timeline_db_path: Optional[str] = None,
    **kwargs
) -> WhereWasEyeAgent:
    """
    Create a WhereWasEyeAgent with simplified configuration.
    
    Args:
        provider: AI provider ("openai" or "ollama")
        model: Model name to use
        timeline_db_path: Path to timeline JSON file
        **kwargs: Additional configuration options
        
    Returns:
        Configured WhereWasEyeAgent instance
    """
    config = AgentConfig(
        provider=provider,
        model=model,
        timeline_db_path=timeline_db_path,
        **kwargs
    )
    return WhereWasEyeAgent(config)