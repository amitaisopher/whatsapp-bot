from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    message: str = Field(..., description="User's message")
    session_id: str | None = Field(None, description="Conversation session ID")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Representative's response")
    cars: list[dict] | None = Field(None, description="Matching cars if found")
    session_id: str = Field(..., description="Conversation session ID")
    escalation_needed: bool = Field(
        False, description="Whether human intervention is needed")