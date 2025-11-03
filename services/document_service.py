import uuid
from typing import List
import PyPDF2
from docx import Document
import google.generativeai as genai
from services.typesense_client import TypesenseClient
from utils.config import config
from utils.constants import DEFAULT_CHUNK_SIZE, EMBEDDING_TASK_DOCUMENT

class DocumentService:
    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.typesense = TypesenseClient()
        
    async def process_document(self, filename: str, content: bytes) -> str:
        doc_id = str(uuid.uuid4())
        
        text = self.extract_text(filename, content)
        chunks = self.split_text(text)
        await self.index_chunks(doc_id, filename, chunks)
        
        return doc_id
    
    def extract_text(self, filename: str, content: bytes) -> str:
        if filename.endswith('.pdf'):
            return self.extract_pdf_text(content)
        elif filename.endswith('.docx'):
            return self.extract_docx_text(content)
        else:
            return content.decode('utf-8')
    
    def extract_pdf_text(self, content: bytes) -> str:
        from io import BytesIO
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    
    def extract_docx_text(self, content: bytes) -> str:
        from io import BytesIO
        doc = Document(BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def split_text(self, text: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[str]:
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            if current_size + len(word) > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    async def index_chunks(self, doc_id: str, filename: str, chunks: List[str]):
        for i, chunk in enumerate(chunks):
            embedding = self.generate_embedding(chunk)
            
            document = {
                'id': f"{doc_id}_{i}",
                'doc_id': doc_id,
                'filename': filename,
                'chunk_index': i,
                'content': chunk,
                'embedding': embedding
            }
            
            await self.typesense.index_document(document)
    
    def generate_embedding(self, text: str) -> List[float]:
        result = genai.embed_content(
            model=config.GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type=EMBEDDING_TASK_DOCUMENT
        )
        return result['embedding']
