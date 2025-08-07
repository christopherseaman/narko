#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "requests", 
#     "python-dotenv",
# ]
# ///
"""
Test external file import functionality for Notion API
Based on https://developers.notion.com/docs/importing-external-files
"""
import os
import time
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()
NOTION_API_KEY = os.getenv('NOTION_API_KEY')

def test_external_import():
    """Test external file import using indirect import method"""
    if not NOTION_API_KEY:
        print("❌ No API key found")
        return
    
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Test with a reliable external image
    external_url = "https://httpbin.org/image/jpeg"
    filename = "test_external.jpg"
    
    print(f"🌐 Testing external import from: {external_url}")
    print(f"📄 Filename: {filename}")
    
    # Step 1: Create external file upload
    print("\n1️⃣ Creating external file upload...")
    upload_request = {
        "mode": "external_url",
        "filename": filename,
        "external_url": external_url
    }
    
    response = requests.post(
        "https://api.notion.com/v1/file_uploads",
        headers=headers,
        json=upload_request
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200:
        print("❌ Failed to create external import")
        return None
    
    upload_data = response.json()
    file_id = upload_data.get("id")
    status = upload_data.get("status")
    
    print(f"✅ External import created - ID: {file_id}")
    print(f"📊 Initial status: {status}")
    
    # Step 2: Poll for completion
    print("\n2️⃣ Polling for import completion...")
    max_attempts = 30  # 30 seconds max wait
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        
        # Check status
        status_response = requests.get(
            f"https://api.notion.com/v1/file_uploads/{file_id}",
            headers=headers
        )
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            current_status = status_data.get("status")
            
            print(f"⏳ Attempt {attempt}: Status = {current_status}")
            
            if current_status == "uploaded":
                print("✅ External import completed successfully!")
                print(f"📁 Final data: {status_data}")
                return file_id
            elif current_status == "failed":
                print("❌ External import failed")
                print(f"📄 Error details: {status_data}")
                return None
            elif current_status == "expired":
                print("⏰ External import expired")
                return None
            
            # Still pending, wait and retry
            time.sleep(1)
        else:
            print(f"❌ Status check failed: {status_response.status_code}")
            break
    
    print("⏰ Timeout waiting for external import completion")
    return None

if __name__ == "__main__":
    test_external_import()