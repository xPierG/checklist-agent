import os
import hashlib
from google.genai import types
from google.genai import Client
from docx import Document
from abc import ABC, abstractmethod

class BaseDocumentLoader(ABC):
    """Abstract Base Class for document loaders."""
    def __init__(self, client: Client):
        self.client = client
        self.cache_dir = ".gemini_cache" # Changed from .pdf_cache to .gemini_cache for generality
        os.makedirs(self.cache_dir, exist_ok=True)
        self.uri_cache = {}

    def _calculate_hash(self, data: bytes) -> str:
        """Calculates MD5 hash of the data."""
        hasher = hashlib.md5()
        hasher.update(data)
        return hasher.hexdigest()

    @abstractmethod
    def load_document(self, file_path: str, display_name: str = None) -> str:
        """
        Loads a document, uploads it to Gemini, and returns the URI.
        Caches the URI based on the file's hash to avoid re-uploading.
        """
        pass

class PDFLoader(BaseDocumentLoader):
    """
    Handles uploading and caching of PDF documents for Gemini.
    """
    def load_document(self, file_path: str, display_name: str = None) -> str:
        if not display_name:
            display_name = os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        file_hash = self._calculate_hash(file_content)
        if file_hash in self.uri_cache:
            print(f"Cache hit for {display_name}. Using cached URI.")
            return self.uri_cache[file_hash]

        print(f"Uploading {display_name} (PDF)...")
        file_ref = self.client.files.upload(file=file_path) # Direct upload for PDF
        print(f"Uploaded {display_name} as {file_ref.name}")
        self.uri_cache[file_hash] = file_ref.name
        return file_ref.name

class DocxLoader(BaseDocumentLoader):
    """
    Handles uploading and caching of DOCX documents for Gemini.
    Converts DOCX to plain text before uploading.
    """
    def load_document(self, file_path: str, display_name: str = None) -> str:
        if not display_name:
            display_name = os.path.basename(file_path)

        # Convert docx to text
        doc = Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        text_content = "\n".join(full_text).encode('utf-8')

        file_hash = self._calculate_hash(text_content)
        if file_hash in self.uri_cache:
            print(f"Cache hit for {display_name} (DOCX). Using cached URI.")
            return self.uri_cache[file_hash]

        # Save text content to a temporary file for upload
        temp_txt_path = os.path.join(self.cache_dir, f"{file_hash}.txt")
        with open(temp_txt_path, "wb") as f:
            f.write(text_content)

        print(f"Uploading {display_name} (DOCX converted to TXT)...")
        file_ref = self.client.files.upload(file=temp_txt_path)
        print(f"Uploaded {display_name} as {file_ref.name}")
        self.uri_cache[file_hash] = file_ref.name
        os.remove(temp_txt_path) # Clean up temp file
        return file_ref.name

class TextLoader(BaseDocumentLoader):
    """
    Handles uploading and caching of TXT documents for Gemini.
    """
    def load_document(self, file_path: str, display_name: str = None) -> str:
        if not display_name:
            display_name = os.path.basename(file_path)

        with open(file_path, 'rb') as f:
            file_content = f.read()

        file_hash = self._calculate_hash(file_content)
        if file_hash in self.uri_cache:
            print(f"Cache hit for {display_name} (TXT). Using cached URI.")
            return self.uri_dir[file_hash]

        print(f"Uploading {display_name} (TXT)...")
        file_ref = self.client.files.upload(file=file_path) # Direct upload for TXT
        print(f"Uploaded {display_name} as {file_ref.name}")
        self.uri_cache[file_hash] = file_ref.name
        return file_ref.name

class DocumentLoaderFactory:
    """
    Factory to get the appropriate document loader based on file extension.
    """
    def __init__(self, client: Client):
        self.client = client
        self.loaders = {
            ".pdf": PDFLoader(client),
            ".docx": DocxLoader(client),
            ".txt": TextLoader(client),
        }

    def get_loader(self, file_path: str) -> BaseDocumentLoader:
        file_extension = os.path.splitext(file_path)[1].lower()
        loader = self.loaders.get(file_extension)
        if not loader:
            raise ValueError(f"Unsupported file type: {file_extension}")
        return loader
