DEFAULT_CHUNK_SIZE = 1000
EMBEDDING_DIMENSION = 768

EMBEDDING_TASK_DOCUMENT = "retrieval_document"
EMBEDDING_TASK_QUERY = "retrieval_query"

DEFAULT_SEARCH_LIMIT = 5
CONNECTION_TIMEOUT_SECONDS = 2

DEFAULT_CONVERSATION_LIMIT = 10
DEFAULT_CONTEXT_LIMIT = 3

TYPESENSE_SCHEMA_FIELDS = [
    {'name': 'doc_id', 'type': 'string'},
    {'name': 'filename', 'type': 'string'},
    {'name': 'chunk_index', 'type': 'int32'},
    {'name': 'content', 'type': 'string'},
    {'name': 'embedding', 'type': 'float[]', 'num_dim': EMBEDDING_DIMENSION}
]

CONVERSATIONS_SCHEMA_FIELDS = [
    {'name': 'session_id', 'type': 'string'},
    {'name': 'timestamp', 'type': 'string'},
    {'name': 'question', 'type': 'string'},
    {'name': 'answer', 'type': 'string'},
    {'name': 'sources', 'type': 'string[]'},
    {'name': 'interaction_id', 'type': 'string'}
]

QUERY_ANALYZER_PROMPT = """Analyze this user query and provide:
1. Intent (factual, comparison, explanation, definition)
2. Key concepts (important terms/entities)
3. Query type (simple, complex, multi-part)

Query: {query}
Context: {context}

Respond in format:
Intent: [intent]
Concepts: [concept1, concept2, ...]
Type: [type]"""

ANSWER_SYNTHESIS_PROMPT = """Based on the retrieved documents and conversation context, provide a comprehensive answer.

Query: {query}
Intent: {intent}
Key Concepts: {key_concepts}

Previous Context: {context}

Retrieved Documents:
{doc_context}

Provide a clear, well-sourced answer that addresses the user's query."""
