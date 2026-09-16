import os
import uuid
import logging
from typing import Optional, Tuple
import httpx
from app.core.config import settings

logger = logging.getLogger("freshlens.storage")

BUCKET_NAME = "food-images"

class SupabaseStorageService:
    @staticmethod
    def is_configured() -> bool:
        return bool(settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY)

    @classmethod
    async def upload_image(
        cls, file_bytes: bytes, filename: str, content_type: str = "image/jpeg"
    ) -> Tuple[str, str]:
        """
        Uploads image bytes to Supabase Storage 'food-images' private bucket.
        Returns tuple of (storage_path, relative_access_url).
        Falls back to local file path if Supabase Storage is not configured.
        """
        ext = os.path.splitext(filename)[1].lower() or ".jpg"
        storage_path = f"uploads/{uuid.uuid4()}{ext}"

        if not cls.is_configured():
            logger.info("Supabase Storage credentials missing. Using local storage fallback.")
            return storage_path, f"/static/uploads/{os.path.basename(storage_path)}"

        upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
            "apiKey": settings.SUPABASE_SECRET_KEY,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(upload_url, headers=headers, content=file_bytes)
            if response.status_code not in (200, 201):
                logger.error(f"Supabase upload failed [{response.status_code}]: {response.text}")
                raise RuntimeError(f"Failed to upload image to Supabase Storage: {response.text}")

        # Relative access URL pointing to FastAPI authenticated download proxy
        access_url = f"/api/v1/storage/image/{storage_path}"
        return storage_path, access_url

    @classmethod
    async def download_image(cls, storage_path: str) -> Tuple[bytes, str]:
        """
        Retrieves image bytes from Supabase Storage private 'food-images' bucket
        using backend server-side secret key authorization.
        Returns (file_bytes, content_type).
        """
        if not cls.is_configured():
            raise RuntimeError("Supabase Storage credentials not configured on backend.")

        download_url = f"{settings.SUPABASE_URL}/storage/v1/object/authenticated/{BUCKET_NAME}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
            "apiKey": settings.SUPABASE_SECRET_KEY,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(download_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Supabase download failed [{response.status_code}]: {response.text}")
                raise RuntimeError(f"Failed to retrieve image from Supabase Storage: {response.text}")

            content_type = response.headers.get("content-type", "image/jpeg")
            return response.content, content_type

    @classmethod
    async def delete_image(cls, storage_path: str) -> bool:
        """
        Deletes an image from the 'food-images' private bucket.
        """
        if not cls.is_configured():
            return False

        delete_url = f"{settings.SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SECRET_KEY}",
            "apiKey": settings.SUPABASE_SECRET_KEY,
            "Content-Type": "application/json",
        }
        payload = {"prefixes": [storage_path]}

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request("DELETE", delete_url, headers=headers, json=payload)
            return response.status_code == 200
