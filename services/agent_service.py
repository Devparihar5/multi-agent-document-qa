from typing import Dict, Any
import google.generativeai as genai
from langgraph.graph import StateGraph, END
from schema.agent_state import AgentState
from services.typesense_client import TypesenseClient
from services.memory_service import MemoryService
from utils.config import config
from utils.constants import EMBEDDING_TASK_QUERY, QUERY_ANALYZER_PROMPT, ANSWER_SYNTHESIS_PROMPT

class AgentService:
    def __init__(self, memory_service: MemoryService):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        self.typesense = TypesenseClient()
        self.memory = memory_service
        self.graph = self.create_agent_graph()
    
    def create_agent_graph(self):
        workflow = StateGraph(AgentState)
        
        # Add agent nodes
        workflow.add_node("query_analyzer", self.query_analyzer_agent)
        workflow.add_node("search_strategy", self.search_strategy_agent)
        workflow.add_node("document_retrieval", self.document_retrieval_agent)
        workflow.add_node("answer_synthesis", self.answer_synthesis_agent)
        
        # Define the flow
        workflow.set_entry_point("query_analyzer")
        workflow.add_edge("query_analyzer", "search_strategy")
        workflow.add_edge("search_strategy", "document_retrieval")
        workflow.add_edge("document_retrieval", "answer_synthesis")
        workflow.add_edge("answer_synthesis", END)
        
        return workflow.compile()
    
    async def query_analyzer_agent(self, state: AgentState) -> AgentState:
        """Analyzes user query to understand intent and extract key concepts"""
        prompt = QUERY_ANALYZER_PROMPT.format(
            query=state["original_query"],
            context=state["conversation_context"]
        )
        
        response = self.model.generate_content(prompt)
        analysis = response.text
        
        lines = analysis.split('\n')
        intent = lines[0].split(': ')[1] if len(lines) > 0 else "factual"
        concepts = lines[1].split(': ')[1].split(', ') if len(lines) > 1 else []
        query_type = lines[2].split(': ')[1] if len(lines) > 2 else "simple"
        
        state["intent"] = intent
        state["key_concepts"] = concepts
        state["query_type"] = query_type
        state["processing_steps"].append("query_analyzed")
        
        return state
    
    async def search_strategy_agent(self, state: AgentState) -> AgentState:
        """Determines optimal search strategy based on query analysis"""
        if state["query_type"] == "complex":
            strategy = "hybrid_semantic_first"
            params = {"limit": 10, "semantic_weight": 0.7}
        elif state["intent"] == "definition":
            strategy = "semantic_focused"
            params = {"limit": 5, "semantic_weight": 0.9}
        else:
            strategy = "balanced_hybrid"
            params = {"limit": 7, "semantic_weight": 0.5}
        
        state["search_strategy"] = strategy
        state["search_params"] = params
        state["processing_steps"].append("strategy_determined")
        
        return state
    
    async def document_retrieval_agent(self, state: AgentState) -> AgentState:
        """Executes search and retrieves relevant documents"""
        query_embedding = self.generate_query_embedding(state["original_query"])
        
        if state["search_strategy"] == "semantic_focused":
            search_results = await self.semantic_search(state["original_query"], query_embedding, state["search_params"]["limit"])
        else:
            search_results = await self.hybrid_search(state["original_query"], query_embedding, state["search_params"]["limit"])
        
        state["retrieved_docs"] = search_results
        state["search_results"] = search_results
        state["processing_steps"].append("documents_retrieved")
        
        return state
    
    async def answer_synthesis_agent(self, state: AgentState) -> AgentState:
        """Synthesizes final answer from retrieved documents and context"""
        doc_context = "\n\n".join([
            f"Source: {doc['filename']}\nContent: {doc['content']}"
            for doc in state["retrieved_docs"]
        ])
        
        prompt = ANSWER_SYNTHESIS_PROMPT.format(
            query=state["original_query"],
            intent=state["intent"],
            key_concepts=', '.join(state["key_concepts"]),
            context=state["conversation_context"],
            doc_context=doc_context
        )
        
        response = self.model.generate_content(prompt)
        
        state["final_answer"] = response.text
        state["sources"] = list(set([doc['filename'] for doc in state["retrieved_docs"]]))
        state["processing_steps"].append("answer_synthesized")
        
        return state
    
    def generate_query_embedding(self, query: str):
        result = genai.embed_content(
            model=config.GEMINI_EMBEDDING_MODEL,
            content=query,
            task_type=EMBEDDING_TASK_QUERY
        )
        return result['embedding']
    
    async def semantic_search(self, query: str, embedding, limit: int):
        return await self.typesense.hybrid_search(query, embedding, limit)
    
    async def hybrid_search(self, query: str, embedding, limit: int):
        return await self.typesense.hybrid_search(query, embedding, limit)
    
    async def process_query(self, question: str, session_id: str) -> Dict[str, Any]:
        """Main entry point for processing queries through agent workflow"""
        context = self.memory.get_context_for_question(session_id, question)
        
        initial_state = {
            "original_query": question,
            "session_id": session_id,
            "conversation_context": context,
            "intent": None,
            "key_concepts": [],
            "query_type": None,
            "search_strategy": None,
            "search_params": {},
            "retrieved_docs": [],
            "search_results": [],
            "final_answer": None,
            "sources": [],
            "processing_steps": []
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        self.memory.add_interaction(
            session_id, 
            question, 
            final_state["final_answer"], 
            final_state["sources"]
        )
        
        return {
            "answer": final_state["final_answer"],
            "session_id": session_id,
            "processing_steps": final_state["processing_steps"],
            "agent_analysis": {
                "intent": final_state["intent"],
                "key_concepts": final_state["key_concepts"],
                "search_strategy": final_state["search_strategy"]
            }
        }
