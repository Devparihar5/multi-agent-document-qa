import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
        self.GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
        
        self.TYPESENSE_API_KEY = os.getenv("TYPESENSE_API_KEY", "xyz")
        self.TYPESENSE_HOST = os.getenv("TYPESENSE_HOST", "localhost")
        self.TYPESENSE_PORT = int(os.getenv("TYPESENSE_PORT", "8108"))
        self.TYPESENSE_PROTOCOL = os.getenv("TYPESENSE_PROTOCOL", "http")
        
        self.UPLOAD_DIR = "uploads"
        self.COLLECTION_NAME = "documents"
        self.CONVERSATIONS_COLLECTION = "conversations"

config = Config()
