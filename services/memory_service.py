from typing import Dict, List, Any
from datetime import datetime
from services.typesense_client import TypesenseClient
from utils.config import config
from utils.constants import (
    DEFAULT_CONVERSATION_LIMIT, 
    DEFAULT_CONTEXT_LIMIT,
    CONVERSATIONS_SCHEMA_FIELDS
)

class MemoryService:
    def __init__(self):
        self.typesense = TypesenseClient()
        self.ensure_memory_collections()
    
    def ensure_memory_collections(self):
        """Create Typesense collections for memory storage"""
        try:
            self.typesense.client.collections[config.CONVERSATIONS_COLLECTION].retrieve()
        except Exception as e:
            conversation_schema = {
                'name': config.CONVERSATIONS_COLLECTION,
                'fields': CONVERSATIONS_SCHEMA_FIELDS
            }
            self.typesense.client.collections.create(conversation_schema)
    
    def add_interaction(self, session_id: str, question: str, answer: str, sources: List[str]):
        timestamp = datetime.utcnow().isoformat()
        interaction = {
            'session_id': session_id,
            'timestamp': timestamp,
            'question': question,
            'answer': answer,
            'sources': sources,
            'interaction_id': f"{session_id}_{datetime.utcnow().timestamp()}"
        }
        
        try:
            self.typesense.client.collections[config.CONVERSATIONS_COLLECTION].documents.create(interaction)
        except Exception as e:
            pass
    
    def get_conversation_history(self, session_id: str, limit: int = DEFAULT_CONVERSATION_LIMIT) -> List[Dict]:
        search_params = {
            'q': '*',
            'filter_by': f'session_id:={session_id}',
            'per_page': limit
        }
        
        try:
            results = self.typesense.client.collections[config.CONVERSATIONS_COLLECTION].documents.search(search_params)
            history = [hit['document'] for hit in results['hits']]
            return history
        except Exception as e:
            return []
    
    def get_context_for_question(self, session_id: str, current_question: str) -> str:
        history = self.get_conversation_history(session_id, limit=DEFAULT_CONTEXT_LIMIT)
        
        if not history:
            return ""
        
        context_parts = []
        for interaction in history:
            context_parts.append(f"Previous Q: {interaction['question']}")
            context_parts.append(f"Previous A: {interaction['answer'][:200]}...")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str):
        try:
            self.typesense.client.collections[config.CONVERSATIONS_COLLECTION].documents.delete({
                'filter_by': f'session_id:={session_id}'
            })
        except:
            pass
