"""
API endpoints for agent.
"""
from typing import Dict, Optional, Any
import uuid
import logging
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.agent_service import get_agent_service, AgentService

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define request and response models
class AgentRequest(BaseModel):
    """Request model for agent interactions."""
    message: str = Field(..., description="User message to the agent")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")

class AgentResponse(BaseModel):
    """Response model for agent interactions."""
    response: Dict[str, Any] = Field(..., description="Agent response")
    thread_id: str = Field(..., description="Thread ID for this conversation")

# Create router
router = APIRouter(tags=["agent"])

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> AgentResponse:
    """Chat with the ReAct agent.
    
    Args:
        request: The chat request containing the user message and optional thread_id
        agent_service: The agent service dependency
        
    Returns:
        The agent's response and the thread_id
    """
    try:
        # Utiliser le thread_id fourni ou laisser le service en générer un
        thread_id = request.thread_id
        logger.debug(f"API /chat endpoint received thread_id: {thread_id}")
        
        # Invoquer l'agent
        response = agent_service.invoke_agent(request.message, thread_id)
        
        # Récupérer le thread_id utilisé (qui peut être nouveau si aucun n'était fourni)
        used_thread_id = thread_id or response.get("thread_id", str(uuid.uuid4()))
        logger.debug(f"API /chat endpoint using thread_id: {used_thread_id}")
        
        return AgentResponse(
            response=response,
            thread_id=used_thread_id
        )
    except Exception as e:
        logger.error(f"Error in chat_with_agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@router.post("/continue", response_model=AgentResponse)
async def continue_conversation(
    request: AgentRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> AgentResponse:
    """Continue an existing conversation with the agent.
    
    Args:
        request: The chat request containing the user message and thread_id
        agent_service: The agent service dependency
        
    Returns:
        The agent's response and the thread_id
    """
    try:
        # Thread ID is required for continuation
        if not request.thread_id:
            logger.error("Thread ID missing in continue request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thread ID is required to continue a conversation"
            )
        
        logger.debug(f"API /continue endpoint with thread_id: {request.thread_id}")
        
        # Continue the conversation
        response = agent_service.continue_conversation(request.message, request.thread_id)
        
        return AgentResponse(
            response=response,
            thread_id=request.thread_id
        )
    except ValueError as ve:
        logger.error(f"Value error in continue_conversation: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Error in continue_conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )