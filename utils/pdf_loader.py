import os
import hashlib
from google.genai import types
from google.genai import Client

class PDFLoader:
    """
    Handles uploading and caching of PDF documents for Gemini.
    """
    def __init__(self, client: Client):
        self.client = client
        self.cache_dir = ".pdf_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.uri_cache = {}

    def _calculate_hash(self, file_path: str) -> str:
        """Calculates MD5 hash of the file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def upload_and_cache(self, file_path: str, display_name: str = None) -> str:
        """
        Uploads a PDF to Gemini and returns the URI.
        Caches the URI based on the file's hash to avoid re-uploading.
        """
        if not display_name:
            display_name = os.path.basename(file_path)

        file_hash = self._calculate_hash(file_path)
        if file_hash in self.uri_cache:
            print(f"Cache hit for {display_name}. Using cached URI.")
            return self.uri_cache[file_hash]

        print(f"Uploading {display_name}...")
        
        # Upload the file
        file_ref = self.client.files.upload(file=file_path)
        
        print(f"Uploaded {display_name} as {file_ref.name}")
        
        # Store in cache
        self.uri_cache[file_hash] = file_ref.name
        
        return file_ref.name

    def get_file_content(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            return f.read()
