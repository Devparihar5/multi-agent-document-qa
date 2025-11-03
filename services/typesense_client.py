import typesense
from typing import List, Dict, Any
from utils.config import config
from utils.constants import CONNECTION_TIMEOUT_SECONDS, TYPESENSE_SCHEMA_FIELDS, DEFAULT_SEARCH_LIMIT

class TypesenseClient:
    def __init__(self):
        self.client = typesense.Client({
            'nodes': [{
                'host': config.TYPESENSE_HOST,
                'port': str(config.TYPESENSE_PORT),
                'protocol': config.TYPESENSE_PROTOCOL
            }],
            'api_key': config.TYPESENSE_API_KEY,
            'connection_timeout_seconds': CONNECTION_TIMEOUT_SECONDS
        })
        self.ensure_collection()
    
    def ensure_collection(self):
        schema = {
            'name': config.COLLECTION_NAME,
            'fields': TYPESENSE_SCHEMA_FIELDS
        }
        
        try:
            self.client.collections[config.COLLECTION_NAME].retrieve()
        except:
            self.client.collections.create(schema)
    
    async def index_document(self, document: Dict[str, Any]):
        self.client.collections[config.COLLECTION_NAME].documents.create(document)
    
    async def hybrid_search(self, query: str, query_embedding: List[float], limit: int = DEFAULT_SEARCH_LIMIT) -> List[Dict]:
        """Hybrid search combining keyword and vector search"""
        search_requests = {
            'searches': [
                {
                    'collection': config.COLLECTION_NAME,
                    'q': query,
                    'query_by': 'content',
                    'vector_query': f'embedding:([{",".join(map(str, query_embedding))}], k:{limit})',
                    'per_page': limit,
                    'include_fields': 'doc_id,filename,content,chunk_index'
                }
            ]
        }
        
        try:
            results = self.client.multi_search.perform(search_requests, {})
            hits = results['results'][0]['hits'] if results['results'] else []
        except:
            search_params = {
                'q': query,
                'query_by': 'content',
                'per_page': limit,
                'include_fields': 'doc_id,filename,content,chunk_index'
            }
            results = self.client.collections[config.COLLECTION_NAME].documents.search(search_params)
            hits = results['hits']
        
        return [
            {
                'content': hit['document']['content'],
                'filename': hit['document']['filename'],
                'doc_id': hit['document']['doc_id'],
                'score': hit.get('text_match_info', {}).get('score', 0)
            }
            for hit in hits
        ]
