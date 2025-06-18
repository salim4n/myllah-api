"""
Tests for the agent service.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.agent_service import AgentService, get_agent_service


class TestAgentService:
    """Test cases for the AgentService class."""
    
    def test_get_weather(self):
        """Test the get_weather tool."""
        service = AgentService()
        result = service.get_weather("Paris")
        assert result == "It's always sunny in Paris!"
    
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatOpenAI")
    @patch("app.services.agent_service.settings")
    def test_agent_initialization(self, mock_settings, mock_chat_openai, mock_create_agent):
        """Test that the agent is properly initialized."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_model = MagicMock()
        mock_chat_openai.return_value = mock_model
        mock_create_agent.return_value = mock_agent
        mock_settings.OPENAI_API_KEY = "test-api-key"
        
        # Create service
        service = AgentService()
        
        # Verify model was created with correct parameters
        mock_chat_openai.assert_called_once_with(model="o4-mini", api_key="test-api-key")
        
        # Verify agent was created with correct parameters
        mock_create_agent.assert_called_once()
        args, kwargs = mock_create_agent.call_args
        assert kwargs["model"] == mock_model
        assert len(kwargs["tools"]) == 1
        assert kwargs["checkpointer"] is not None
    
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatOpenAI")
    @patch("app.services.agent_service.settings")
    def test_invoke_agent(self, mock_settings, mock_chat_openai, mock_create_agent):
        """Test invoking the agent."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_model = MagicMock()
        mock_agent.invoke.return_value = {"response": "test response"}
        mock_chat_openai.return_value = mock_model
        mock_create_agent.return_value = mock_agent
        
        # Create service and invoke agent
        service = AgentService()
        response = service.invoke_agent("Hello", "test-thread")
        
        # Verify agent was invoked with correct parameters
        mock_agent.invoke.assert_called_once()
        args, kwargs = mock_agent.invoke.call_args
        assert args[0]["messages"][0]["content"] == "Hello"
        assert kwargs["configurable"]["thread_id"] == "test-thread"
        assert response == {"response": "test response"}
    
    @patch("app.services.agent_service.create_react_agent")
    @patch("app.services.agent_service.ChatOpenAI")
    @patch("app.services.agent_service.settings")
    def test_continue_conversation(self, mock_settings, mock_chat_openai, mock_create_agent):
        """Test continuing a conversation with the agent."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_model = MagicMock()
        mock_agent.invoke.return_value = {"response": "follow-up response"}
        mock_chat_openai.return_value = mock_model
        mock_create_agent.return_value = mock_agent
        
        # Create service and continue conversation
        service = AgentService()
        response = service.continue_conversation("Tell me more", "existing-thread")
        
        # Verify agent was invoked with correct parameters
        mock_agent.invoke.assert_called_once()
        args, kwargs = mock_agent.invoke.call_args
        assert args[0]["messages"][0]["content"] == "Tell me more"
        assert kwargs["configurable"]["thread_id"] == "existing-thread"
        assert response == {"response": "follow-up response"}
    
    @pytest.mark.asyncio
    async def test_get_agent_service_singleton(self):
        """Test that get_agent_service returns a singleton instance."""
        service1 = await get_agent_service()
        service2 = await get_agent_service()
        assert service1 is service2
