from fastapi import FastAPI, UploadFile, File, HTTPException

from services.document_service import DocumentService
from services.agent_service import AgentService
from services.memory_service import MemoryService

from schema.qa import QuestionRequest, QuestionResponse

app = FastAPI(title="Smart Document Q&A System")

document_service = DocumentService()
memory_service = MemoryService()
agent_service = AgentService(memory_service)


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await file.read()
        doc_id = await document_service.process_document(file.filename, content)
        return {"message": "Document uploaded successfully", "document_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    try:
        result = await agent_service.process_query(
            question=request.question,
            session_id=request.session_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    try:
        history = memory_service.get_conversation_history(session_id)
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    try:
        memory_service.clear_session(session_id)
        return {"message": f"Session {session_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
