"""
File upload and external import functionality for Notion
"""
import os
import time
import asyncio
import aiohttp
import aiofiles
import requests
import datetime
import mimetypes
import logging
from typing import Dict, Optional, Callable
from ..config import Config
from ..utils.cache import UploadCache
from ..utils.validation import FileValidator

logger = logging.getLogger(__name__)


class FileUploader:
    """Handle direct file uploads to Notion"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cache = UploadCache(config)
        self.validator = FileValidator(config)
    
    async def upload_async(self, file_path: str, file_name: str = None,
                          progress_callback: Optional[Callable] = None) -> Dict:
        """Upload file asynchronously with streaming support

        Automatically applies .txt extension workaround for unsupported text file types
        like .py, .sh, .md that Notion's API doesn't accept natively.
        """
        if not file_name:
            file_name = os.path.basename(file_path)

        original_name = file_name
        file_ext = os.path.splitext(file_name)[1].lower()

        # Check if file needs extension workaround
        needs_workaround = self.config.needs_extension_workaround(file_ext)
        if needs_workaround:
            # Add .txt extension for upload
            file_name = f"{file_name}.txt"
            logger.info(f"Applying .txt workaround: {original_name} -> {file_name}")

        # Validate file
        validation = self.validator.validate_file(file_path)
        if not validation['valid']:
            return {'error': f'Validation failed: {validation["errors"]}', 'file_path': file_path}

        file_size = validation['metadata']['size']
        
        # Check cache
        file_hash = validation['metadata'].get('hash')
        if file_hash and self.cache.is_enabled:
            cached_result = self.cache.get(file_hash)
            if cached_result:
                cached_result["from_cache"] = True
                logger.info(f"Cache hit for {file_name}")
                return cached_result
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.config.notion_api_key}",
                    "Notion-Version": self.config.notion_version
                }
                
                # Step 1: Create file upload request
                create_data = {"name": file_name, "size": file_size}
                
                async with session.post(
                    "https://api.notion.com/v1/file_uploads",
                    headers=headers,
                    json=create_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as create_response:
                    
                    if create_response.status != 200:
                        error_text = await create_response.text()
                        return {'error': f'Failed to create upload (status {create_response.status}): {error_text[:200]}'}
                    
                    upload_data = await create_response.json()
                    upload_url = upload_data.get("upload_url")
                    file_id = upload_data.get("id")
                    
                    if not upload_url or not file_id:
                        return {'error': 'Invalid upload response from Notion API'}
                
                # Step 2: Upload file content
                # Check if we got a direct upload URL or need to use the /send endpoint
                if not upload_url:
                    # Use the /send endpoint
                    upload_url = f"https://api.notion.com/v1/file_uploads/{file_id}/send"

                upload_result = await self._upload_file_content(
                    session, upload_url, file_path, file_name, file_size, progress_callback
                )
                
                if 'error' in upload_result:
                    return upload_result
                
                # Success - create result
                result = {
                    "file_id": file_id,
                    "name": file_name,
                    "original_name": original_name if needs_workaround else file_name,
                    "size": file_size,
                    "success": True,
                    "upload_timestamp": datetime.datetime.utcnow().isoformat(),
                    "upload_method": "direct",
                    "workaround_applied": needs_workaround
                }
                
                # Cache result
                if file_hash and self.cache.is_enabled:
                    self.cache.set(file_hash, result)
                
                return result
                
        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            return {'error': f'Upload failed: {str(e)}', 'file_path': file_path}
    
    async def _upload_file_content(self, session: aiohttp.ClientSession, upload_url: str, 
                                  file_path: str, file_name: str, file_size: int,
                                  progress_callback: Optional[Callable] = None) -> Dict:
        """Upload file content to the provided upload URL"""
        try:
            # Detect proper MIME type
            mime_type = self._get_mime_type(file_name)
            
            # Upload URL needs authorization headers
            upload_headers = {
                "Authorization": f"Bearer {self.config.notion_api_key}",
                "Notion-Version": self.config.notion_version
            }
            
            if file_size > self.config.stream_chunk_size:
                # Streaming upload for large files
                return await self._stream_upload(session, upload_url, upload_headers, 
                                               file_path, file_name, mime_type, file_size, progress_callback)
            else:
                # Simple upload for small files
                return await self._simple_upload(session, upload_url, upload_headers, 
                                                file_path, file_name, mime_type)
                
        except Exception as e:
            return {'error': f'Upload content failed: {str(e)}'}
    
    async def _simple_upload(self, session: aiohttp.ClientSession, upload_url: str,
                           headers: Dict, file_path: str, file_name: str, mime_type: str) -> Dict:
        """Simple file upload for smaller files"""
        try:
            # Check if this is a /send endpoint (new API) or S3 presigned URL
            if '/send' in upload_url:
                # New API endpoint - use multipart/form-data
                async with aiofiles.open(file_path, 'rb') as f:
                    file_data = await f.read()

                data = aiohttp.FormData()
                data.add_field('file', file_data, filename=file_name, content_type=mime_type)

                # Don't send Content-Type header for multipart
                upload_headers = {k: v for k, v in headers.items() if k != 'Content-Type'}
            else:
                # S3 presigned URL - use raw file data
                async with aiofiles.open(file_path, 'rb') as f:
                    file_data = await f.read()

                data = file_data
                upload_headers = headers.copy()
                upload_headers['Content-Type'] = mime_type

            async with session.post(upload_url, headers=upload_headers, data=data,
                                  timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status not in [200, 201, 204]:  # 204 for successful S3 uploads
                    error_text = await response.text()
                    return {'error': f'Upload failed (status {response.status}): {error_text[:200]}'}

                return {'success': True}

        except Exception as e:
            return {'error': f'Simple upload failed: {str(e)}'}
    
    async def _stream_upload(self, session: aiohttp.ClientSession, upload_url: str, 
                           headers: Dict, file_path: str, file_name: str, mime_type: str,
                           file_size: int, progress_callback: Optional[Callable] = None) -> Dict:
        """Streaming upload for larger files with progress reporting"""
        try:
            uploaded_bytes = 0
            
            async with aiofiles.open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                
                async def file_sender():
                    nonlocal uploaded_bytes
                    while chunk := await f.read(self.config.stream_chunk_size):
                        uploaded_bytes += len(chunk)
                        if progress_callback:
                            progress = uploaded_bytes / file_size
                            progress_callback(file_name, progress)
                        yield chunk
                
                data.add_field('file', file_sender(), filename=file_name, content_type=mime_type)
                
                async with session.post(upload_url, headers=headers, data=data, 
                                      timeout=aiohttp.ClientTimeout(total=300)) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        return {'error': f'Streaming upload failed (status {response.status}): {error_text[:200]}'}
                    
                    if progress_callback:
                        progress_callback(file_name, 1.0)  # Complete
                    
                    return {'success': True}
                    
        except Exception as e:
            return {'error': f'Streaming upload failed: {str(e)}'}
    
    def _get_mime_type(self, file_name: str) -> str:
        """Get Notion-compatible MIME type

        For files with .txt workaround, always returns text/plain
        """
        ext = os.path.splitext(file_name)[1].lower()

        # If file has .txt extension (including workaround files), use text/plain
        if ext == '.txt':
            return 'text/plain'

        mime_type = self.config.get_mime_type(ext)

        # Fallback to system detection if not in our mapping
        if mime_type == 'application/octet-stream':
            detected_type, _ = mimetypes.guess_type(file_name)
            if detected_type:
                mime_type = detected_type

        return mime_type
    
    def upload_sync(self, file_path: str, file_name: str = None) -> Dict:
        """Synchronous wrapper for upload"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.upload_async(file_path, file_name))


class ExternalImporter:
    """Handle external file imports using Notion's indirect import method"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def import_file(self, external_url: str, filename: str = None) -> Dict:
        """Import external file using Notion's indirect import method"""
        if not filename:
            filename = self._extract_filename_from_url(external_url)
        
        headers = {
            "Authorization": f"Bearer {self.config.notion_api_key}",
            "Content-Type": "application/json", 
            "Notion-Version": self.config.notion_version
        }
        
        logger.info(f"Starting external import: {external_url} -> {filename}")
        
        try:
            # Step 1: Create external file upload
            upload_request = {
                "mode": "external_url",
                "filename": filename,
                "external_url": external_url
            }
            
            response = requests.post(
                "https://api.notion.com/v1/file_uploads",
                headers=headers,
                json=upload_request,
                timeout=30
            )
            
            if response.status_code != 200:
                error_data = response.text
                logger.error(f"External import creation failed: {response.status_code} - {error_data}")
                return {"error": f"External import failed: {error_data[:200]}"}
            
            upload_data = response.json()
            file_id = upload_data.get("id")
            
            if not file_id:
                return {"error": "No file ID returned from external import request"}
            
            # Step 2: Poll for completion
            return self._poll_for_completion(file_id, filename, external_url, headers)
            
        except Exception as e:
            logger.error(f"External import error for {external_url}: {e}")
            return {"error": f"External import failed: {str(e)}"}
    
    def _extract_filename_from_url(self, external_url: str) -> str:
        """Extract meaningful filename from URL"""
        base_url = external_url.split('?')[0]  # Remove query parameters
        extracted_name = os.path.basename(base_url)
        
        # If no extension found or invalid filename, create a meaningful one
        if not extracted_name or '.' not in extracted_name:
            # Try to infer from URL path
            if 'image' in external_url.lower():
                if 'jpeg' in external_url.lower() or 'jpg' in external_url.lower():
                    return "image.jpg"
                elif 'png' in external_url.lower():
                    return "image.png"
                elif 'gif' in external_url.lower():
                    return "image.gif"
                else:
                    return "image.jpg"  # Default to jpg
            else:
                return "external_file.bin"
        else:
            return extracted_name
    
    def _poll_for_completion(self, file_id: str, filename: str, external_url: str, headers: Dict) -> Dict:
        """Poll for external import completion"""
        logger.info(f"Polling for external import completion: {file_id}")
        max_attempts = 30  # 30 seconds max wait
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            status_response = requests.get(
                f"https://api.notion.com/v1/file_uploads/{file_id}",
                headers=headers,
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                current_status = status_data.get("status")
                
                if current_status == "uploaded":
                    logger.info(f"External import completed: {filename}")
                    return {
                        "file_id": file_id,
                        "name": filename,
                        "size": status_data.get("content_length", 0),
                        "success": True,
                        "external_url": external_url,
                        "import_method": "external",
                        "upload_timestamp": datetime.datetime.utcnow().isoformat(),
                        "content_type": status_data.get("content_type")
                    }
                elif current_status == "failed":
                    logger.error(f"External import failed for {filename}")
                    return {"error": "External import failed - file could not be imported from URL"}
                elif current_status == "expired":
                    logger.error(f"External import expired for {filename}")
                    return {"error": "External import expired"}
            
            # Still pending, wait and retry
            time.sleep(1)
        
        logger.error(f"External import timeout for {filename}")
        return {"error": "External import timeout - file did not complete within 30 seconds"}