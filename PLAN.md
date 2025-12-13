# Plan: Implement Caching in PDFLoader

This plan outlines the steps to implement a caching mechanism in `PDFLoader` to avoid redundant file uploads.

## 1. Modify `PDFLoader` in `utils/pdf_loader.py`

- [ ] **Add a cache dictionary:** Introduce an instance variable `self.uri_cache = {}` in the `__init__` method to store file hashes and their corresponding URIs.
- [ ] **Modify `upload_and_cache` method:**
    - Calculate the MD5 hash of the file being uploaded.
    - Check if the hash exists as a key in `self.uri_cache`.
    - If the hash is found, return the cached URI and log a message indicating a cache hit.
    - If the hash is not found, proceed with uploading the file, store the new URI in the cache with the hash as the key, and then return the URI.

## 2. Verification

- [ ] **Review the code changes:** Ensure the implementation is correct and follows best practices.
- [ ] **Propose manual testing:** Provide instructions to the user on how to manually verify that the caching is working as expected (e.g., by observing the logs or the speed of processing the same file multiple times).
