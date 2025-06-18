"""Agent service module for handling ReAct agent interactions."""

from typing import Dict, Any
import uuid
from langgraph.prebuilt import create_react_agent 
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class AgentService:
    """Service for handling ReAct agent interactions."""
    
    def __init__(self):
        """Initialize the agent service with basic components."""
        # Create an in-memory saver for checkpointing conversations
        self.checkpointer = InMemorySaver()
        
        # Get API key from settings and clean it
        api_key = settings.OPENAI_API_KEY
        
        # Initialize the model with the cleaned API key
        self.model = ChatOpenAI(model="gpt-4.1-mini", api_key=api_key)

        self.client = MultiServerMCPClient(
    {
        "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory",
      ],
      "transport": "stdio",
      "env": {}
        },
        "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ],
      "transport": "stdio",
      "env": {}
    },
    }
)
        # Agent will be initialized in the setup method
        self.tools = None
        self.agent = None
        
    @classmethod
    async def create(cls):
        """Asynchronous factory method to create and initialize the agent service.
        
        Returns:
            An initialized AgentService instance
        """
        service = cls()
        # Define tools that the agent can use
        service.tools = await service.client.get_tools()
        
        # Initialize the agent with the model
        service.agent = create_react_agent(
            model=service.model, 
            tools=service.tools,
            checkpointer=service.checkpointer,
        )
        
        return service
    
    def get_weather(self, city: str) -> str:
        """Get weather for a given city.
        
        Args:
            city: The city to get weather for
            
        Returns:
            A string describing the weather
        """
        return f"It's always sunny in {city}!"
    
    def invoke_agent(self, message: str, thread_id: str = None) -> Dict[str, Any]:
        """Invoke the agent with a user message.
        
        Args:
            message: The user message to process
            thread_id: The thread ID for conversation continuity
            
        Returns:
            The agent's response
        """
        # Générer un thread_id unique s'il n'est pas fourni
        if thread_id is None:
            thread_id = str(uuid.uuid4())
            logger.debug(f"Generated new thread_id: {thread_id}")
        else:
            logger.debug(f"Using provided thread_id: {thread_id}")
            
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        logger.debug(f"Agent config: {config}")
        
        try:
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                config
            )
            logger.debug(f"Agent response keys: {response.keys()}")
            return response
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise
    
    def continue_conversation(self, message: str, thread_id: str) -> Dict[str, Any]:
        """Continue an existing conversation with the agent.
        
        Args:
            message: The new user message
            thread_id: The thread ID of the existing conversation
            
        Returns:
            The agent's response
        """
        if not thread_id:
            logger.error("Thread ID is required for conversation continuation")
            raise ValueError("Thread ID is required for conversation continuation")
            
        logger.debug(f"Continuing conversation with thread_id: {thread_id}")
        
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        logger.debug(f"Continue config: {config}")
        
        try:
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": message}]},
                config
            )
            logger.debug(f"Continue response keys: {response.keys()}")
            return response
        except Exception as e:
            logger.error(f"Error continuing conversation: {str(e)}")
            raise


# Singleton instance
_agent_service = None


async def get_agent_service() -> AgentService:
    """Get or create the agent service singleton asynchronously.
    
    Returns:
        The agent service instance
    """
    global _agent_service
    if _agent_service is None:
        _agent_service = await AgentService.create()
    return _agent_service