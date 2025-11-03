from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = "default"

class QuestionResponse(BaseModel):
    answer: str
    session_id: str
    processing_steps: Optional[List[str]] = []
    agent_analysis: Optional[Dict[str, Any]] = {}
