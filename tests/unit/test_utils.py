import unittest
import os
import hashlib
from unittest.mock import patch, MagicMock
from utils.logger import AppLogger, logger # Import both for singleton test
from utils.pdf_loader import PDFLoader
from google.genai import Client, types

# Mock for google.genai.types.File
class MockFile:
    def __init__(self, name):
        self.name = name

class TestAppLogger(unittest.TestCase):
    
    def setUp(self):
        # Reset the singleton state before each test
        AppLogger._instance = None
        AppLogger._initialized = False
        self.logger_instance = AppLogger()
        self.logger_instance.clear_activities() # Clear activities before each test

    def test_singleton(self):
        logger1 = AppLogger()
        logger2 = AppLogger()
        self.assertIs(logger1, logger2)
        self.assertIs(self.logger_instance, logger1)

    def test_log_activity_adds_to_log(self):
        self.logger_instance.info("Test message", "Details")
        self.assertEqual(len(self.logger_instance.activity_log), 1)
        self.assertEqual(self.logger_instance.activity_log[0]['message'], "Test message")
        self.assertEqual(self.logger_instance.activity_log[0]['details'], "Details")
        self.assertEqual(self.logger_instance.activity_log[0]['level'], "INFO")

    def test_activity_log_capped(self):
        max_items = self.logger_instance.max_activity_items
        for i in range(max_items + 5):
            self.logger_instance.info(f"Message {i}")
        self.assertEqual(len(self.logger_instance.activity_log), max_items)
        # Check that the oldest messages were removed
        self.assertEqual(self.logger_instance.activity_log[-1]['message'], f"Message 5")

    def test_get_recent_activities(self):
        for i in range(10):
            self.logger_instance.info(f"Message {i}")
        recent = self.logger_instance.get_recent_activities(limit=5)
        self.assertEqual(len(recent), 5)
        self.assertEqual(recent[0]['message'], "Message 9") # Most recent first

    def test_clear_activities(self):
        self.logger_instance.info("Test message")
        self.logger_instance.clear_activities()
        self.assertEqual(len(self.logger_instance.activity_log), 0)

    @patch('logging.Logger.info')
    def test_info_logging(self, mock_log_info):
        self.logger_instance.info("Info message", "Info details")
        mock_log_info.assert_called_with("Info message | Info details")
        self.assertEqual(self.logger_instance.activity_log[0]['level'], "INFO")

    @patch('logging.Logger.info') # success maps to info in standard logging
    def test_success_logging(self, mock_log_info):
        self.logger_instance.success("Success message", "Success details")
        mock_log_info.assert_called_with("Success message | Success details")
        self.assertEqual(self.logger_instance.activity_log[0]['level'], "SUCCESS")

    @patch('logging.Logger.warning')
    def test_warning_logging(self, mock_log_warning):
        self.logger_instance.warning("Warning message")
        mock_log_warning.assert_called_with("Warning message")
        self.assertEqual(self.logger_instance.activity_log[0]['level'], "WARNING")

    @patch('logging.Logger.error')
    def test_error_logging(self, mock_log_error):
        self.logger_instance.error("Error message", "Error details")
        mock_log_error.assert_called_with("Error message | Error details")
        self.assertEqual(self.logger_instance.activity_log[0]['level'], "ERROR")


class TestPDFLoader(unittest.TestCase):

    def setUp(self):
        self.mock_client = MagicMock(spec=Client)
        self.pdf_loader = PDFLoader(self.mock_client)
        
        # Ensure a clean cache for each test
        self.pdf_loader.uri_cache = {}

        # Create a dummy PDF file for testing
        self.dummy_pdf_path = "test_dummy.pdf"
        with open(self.dummy_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1/Root 1 0 R>>startxref\n0\n%%EOF")

    def tearDown(self):
        if os.path.exists(self.dummy_pdf_path):
            os.remove(self.dummy_pdf_path)
        # Clean up any created cache files (though not expected for this mock test)
        if os.path.exists(self.pdf_loader.cache_dir):
            import shutil
            shutil.rmtree(self.pdf_loader.cache_dir)

    def test_calculate_hash(self):
        hash1 = self.pdf_loader._calculate_hash(self.dummy_pdf_path)
        with open(self.dummy_pdf_path, "wb") as f:
            f.write(b"some other content")
        hash2 = self.pdf_loader._calculate_hash(self.dummy_pdf_path)
        self.assertNotEqual(hash1, hash2)
        
        with open(self.dummy_pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\nxref\n0 1\n0000000000 65535 f\ntrailer<</Size 1/Root 1 0 R>>startxref\n0\n%%EOF")
        hash3 = self.pdf_loader._calculate_hash(self.dummy_pdf_path)
        self.assertEqual(hash1, hash3)

    @patch('builtins.print')
    def test_upload_and_cache_new_file(self, mock_print):
        mock_uploaded_file = MockFile(name="files/12345")
        self.mock_client.files.upload.return_value = mock_uploaded_file

        uri = self.pdf_loader.upload_and_cache(self.dummy_pdf_path)

        self.mock_client.files.upload.assert_called_once_with(file=self.dummy_pdf_path)
        self.assertEqual(uri, "files/12345")
        self.assertIn(self.pdf_loader._calculate_hash(self.dummy_pdf_path), self.pdf_loader.uri_cache)

    @patch('builtins.print')
    def test_upload_and_cache_cached_file(self, mock_print):
        mock_uploaded_file = MockFile(name="files/12345")
        
        # Pre-cache a file
        file_hash = self.pdf_loader._calculate_hash(self.dummy_pdf_path)
        self.pdf_loader.uri_cache[file_hash] = "files/cached_uri"

        uri = self.pdf_loader.upload_and_cache(self.dummy_pdf_path)

        # Assert that client.files.upload was NOT called
        self.mock_client.files.upload.assert_not_called()
        self.assertEqual(uri, "files/cached_uri")
        self.assertIn(file_hash, self.pdf_loader.uri_cache)

    def test_get_file_content(self):
        content = self.pdf_loader.get_file_content(self.dummy_pdf_path)
        with open(self.dummy_pdf_path, "rb") as f:
            expected_content = f.read()
        self.assertEqual(content, expected_content)


if __name__ == '__main__':
    unittest.main()