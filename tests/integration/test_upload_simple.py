#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests", 
#     "python-dotenv",
# ]
# ///
"""
Simple test script to debug Notion file upload API
Based on https://developers.notion.com/reference/create-a-file-upload
"""
import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_IMPORT_ROOT = os.getenv('NOTION_IMPORT_ROOT')

def test_file_upload_api():
    """Test the file upload API with minimal example"""
    if not NOTION_API_KEY:
        print("❌ No API key found")
        return
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    print(f"🔑 API Key: {NOTION_API_KEY[:10]}...{NOTION_API_KEY[-10:]}")
    print(f"📄 Testing file upload API...")
    
    # Create a small test file
    test_content = b"Hello, this is a test file for Notion upload!"
    test_filename = "test.txt"
    
    with open(test_filename, "wb") as f:
        f.write(test_content)
    
    file_size = len(test_content)
    print(f"📁 Created test file: {test_filename} ({file_size} bytes)")
    
    # Step 1: Request upload URL
    print("\n1️⃣ Requesting upload URL...")
    upload_request = {
        "name": test_filename,
        "size": file_size
    }
    
    response = requests.post(
        "https://api.notion.com/v1/file_uploads",
        headers=headers,
        json=upload_request
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        print("❌ Failed to get upload URL")
        # Clean up
        os.remove(test_filename)
        return None
    
    upload_data = response.json()
    upload_url = upload_data.get("upload_url")
    file_id = upload_data.get("id")
    
    print(f"✅ Got upload URL and file ID: {file_id}")
    print(f"🔗 Upload URL: {upload_url}")
    
    # Step 2: Upload the file
    print("\n2️⃣ Uploading file...")
    
    # The upload URL is still a Notion API endpoint, so it needs Bearer token
    upload_headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28"
        # Note: Don't set Content-Type for multipart/form-data, let requests handle it
    }
    
    with open(test_filename, "rb") as f:
        files = {"file": (test_filename, f, "text/plain")}
        upload_response = requests.post(upload_url, headers=upload_headers, files=files)
    
    print(f"Upload Status: {upload_response.status_code}")
    print(f"Upload Response: {upload_response.text}")
    
    # Clean up test file
    os.remove(test_filename)
    
    if upload_response.status_code in [200, 201]:
        print("✅ File uploaded successfully!")
        return file_id
    else:
        print("❌ File upload failed")
        return None

if __name__ == "__main__":
    test_file_upload_api()