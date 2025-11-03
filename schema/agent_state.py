from typing import List, Dict, Any, Optional, TypedDict

class AgentState(TypedDict):
    # Input
    original_query: str
    session_id: str
    conversation_context: str
    
    # Query Analysis
    intent: Optional[str]
    key_concepts: List[str]
    query_type: Optional[str]
    
    # Search Strategy
    search_strategy: Optional[str]
    search_params: Dict[str, Any]
    
    # Document Retrieval
    retrieved_docs: List[Dict]
    search_results: List[Dict]
    
    # Answer Synthesis
    final_answer: Optional[str]
    sources: List[str]
    
    # Metadata
    processing_steps: List[str]
