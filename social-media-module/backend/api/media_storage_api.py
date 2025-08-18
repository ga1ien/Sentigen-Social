"""
Media Storage API
Handles file uploads, storage, and management via Supabase Storage
"""

import mimetypes
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from core.env_config import get_config
from core.user_auth import UserContext, get_current_user
from database.supabase_client import SupabaseClient

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/media", tags=["media"])

# Lazy initialization to avoid import-time environment variable issues
_config = None
_supabase_client = None

def get_app_config():
    """Get config with lazy initialization."""
    global _config
    if _config is None:
        _config = get_config()
    return _config

def get_supabase_client():
    """Get Supabase client with lazy initialization."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client

# Supported file types
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
SUPPORTED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/mov", "video/wmv", "video/webm"}
SUPPORTED_DOCUMENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALL_SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES | SUPPORTED_VIDEO_TYPES | SUPPORTED_DOCUMENT_TYPES

# File size limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024  # 25MB


def get_media_type(content_type: str) -> str:
    """Determine media type from content type."""
    if content_type in SUPPORTED_IMAGE_TYPES:
        return "image"
    elif content_type in SUPPORTED_VIDEO_TYPES:
        return "video"
    elif content_type in SUPPORTED_DOCUMENT_TYPES:
        return "document"
    else:
        return "unknown"


def get_max_size_for_type(media_type: str) -> int:
    """Get maximum file size for media type."""
    if media_type == "image":
        return MAX_IMAGE_SIZE
    elif media_type == "video":
        return MAX_VIDEO_SIZE
    elif media_type == "document":
        return MAX_DOCUMENT_SIZE
    else:
        return MAX_IMAGE_SIZE


@router.post("/upload")
async def upload_media(
    files: List[UploadFile] = File(...),
    tags: Optional[str] = Form(None),
    current_user: UserContext = Depends(get_current_user),
) -> Dict[str, Any]:
    """Upload one or more media files to Supabase Storage."""
    try:
        if not files:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

        if len(files) > 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 files allowed per upload")

        logger.info("Starting media upload", user_id=current_user.user_id, file_count=len(files))

        uploaded_files = []
        file_tags = tags.split(",") if tags else []

        for file in files:
            # Validate file type
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0]
            if not content_type or content_type not in ALL_SUPPORTED_TYPES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {content_type}"
                )

            # Read file content
            file_content = await file.read()
            file_size = len(file_content)

            # Validate file size
            media_type = get_media_type(content_type)
            max_size = get_max_size_for_type(media_type)

            if file_size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is too large. Max size for {media_type}: {max_size // (1024*1024)}MB",
                )

            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            storage_path = f"users/{current_user.user_id}/media/{unique_filename}"

            # Upload to Supabase Storage
            try:
                storage_response = get_supabase_client().client.storage.from_("media").upload(
                    path=storage_path,
                    file=file_content,
                    file_options={"content-type": content_type, "cache-control": "3600"},
                )

                if hasattr(storage_response, "error") and storage_response.error:
                    raise Exception(f"Storage upload failed: {storage_response.error}")

                # Get public URL
                public_url_response = get_supabase_client().client.storage.from_("media").get_public_url(storage_path)
                public_url = (
                    public_url_response
                    if isinstance(public_url_response, str)
                    else public_url_response.get("publicUrl")
                )

                # Create media asset record
                media_asset = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user.user_id,
                    "filename": unique_filename,
                    "original_filename": file.filename or unique_filename,
                    "media_type": media_type,
                    "content_type": content_type,
                    "file_size": file_size,
                    "storage_path": storage_path,
                    "public_url": public_url,
                    "tags": file_tags,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }

                # Save to database
                db_result = get_supabase_client().client.table("media_assets").insert(media_asset).execute()

                if not db_result.data:
                    # If database insert fails, try to clean up storage
                    try:
                        get_supabase_client().client.storage.from_("media").remove([storage_path])
                    except:
                        pass
                    raise Exception("Failed to save media asset to database")

                uploaded_files.append(
                    {
                        "id": media_asset["id"],
                        "filename": media_asset["filename"],
                        "original_filename": media_asset["original_filename"],
                        "media_type": media_type,
                        "file_size": file_size,
                        "public_url": public_url,
                        "created_at": media_asset["created_at"],
                    }
                )

                logger.info(
                    "File uploaded successfully", filename=file.filename, media_type=media_type, file_size=file_size
                )

            except Exception as e:
                logger.error("Failed to upload file", filename=file.filename, error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload {file.filename}: {str(e)}",
                )

        return {
            "message": f"Successfully uploaded {len(uploaded_files)} file(s)",
            "files": uploaded_files,
            "total_uploaded": len(uploaded_files),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Media upload failed", user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Media upload failed")


@router.get("/assets")
async def get_media_assets(
    limit: int = 50,
    offset: int = 0,
    media_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: UserContext = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get user's media assets with optional filtering."""
    try:
        logger.info("Getting media assets", user_id=current_user.user_id, limit=limit, offset=offset)

        # Build query
        query = (
            get_supabase_client().client.table("media_assets")
            .select(
                "id, filename, original_filename, media_type, content_type, " "file_size, public_url, tags, created_at"
            )
            .eq("user_id", current_user.user_id)
        )

        # Apply filters
        if media_type and media_type in ["image", "video", "document"]:
            query = query.eq("media_type", media_type)

        if search:
            query = query.ilike("original_filename", f"%{search}%")

        # Apply pagination and ordering
        result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        assets = result.data if result.data else []

        # Get total count
        count_result = (
            get_supabase_client().client.table("media_assets")
            .select("id", count="exact")
            .eq("user_id", current_user.user_id)
            .execute()
        )

        total_count = count_result.count if count_result.count else 0

        return {
            "assets": assets,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(assets) < total_count,
        }

    except Exception as e:
        logger.error("Failed to get media assets", user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve media assets")


@router.delete("/assets/{asset_id}")
async def delete_media_asset(asset_id: str, current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Delete a media asset and its file from storage."""
    try:
        logger.info("Deleting media asset", asset_id=asset_id, user_id=current_user.user_id)

        # Get asset details
        result = (
            get_supabase_client().client.table("media_assets")
            .select("storage_path, filename")
            .eq("id", asset_id)
            .eq("user_id", current_user.user_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

        asset = result.data[0]
        storage_path = asset["storage_path"]

        # Delete from storage
        try:
            get_supabase_client().client.storage.from_("media").remove([storage_path])
        except Exception as e:
            logger.warning("Failed to delete file from storage", storage_path=storage_path, error=str(e))

        # Delete from database
        get_supabase_client().client.table("media_assets").delete().eq("id", asset_id).eq(
            "user_id", current_user.user_id
        ).execute()

        return {"message": "Media asset deleted successfully", "asset_id": asset_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete media asset", asset_id=asset_id, user_id=current_user.user_id, error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete media asset")


@router.get("/storage-info")
async def get_storage_info(current_user: UserContext = Depends(get_current_user)) -> Dict[str, Any]:
    """Get user's storage usage information."""
    try:
        # Get user's media assets summary
        result = (
            get_supabase_client().client.table("media_assets")
            .select("media_type, file_size")
            .eq("user_id", current_user.user_id)
            .execute()
        )

        assets = result.data if result.data else []

        # Calculate storage usage by type
        usage_by_type = {"image": 0, "video": 0, "document": 0}
        total_files = {"image": 0, "video": 0, "document": 0}

        for asset in assets:
            media_type = asset.get("media_type", "unknown")
            file_size = asset.get("file_size", 0)

            if media_type in usage_by_type:
                usage_by_type[media_type] += file_size
                total_files[media_type] += 1

        total_usage = sum(usage_by_type.values())

        # Storage limits (can be configured per user/plan)
        storage_limit = 1024 * 1024 * 1024  # 1GB default

        return {
            "total_usage_bytes": total_usage,
            "total_usage_mb": round(total_usage / (1024 * 1024), 2),
            "storage_limit_bytes": storage_limit,
            "storage_limit_mb": round(storage_limit / (1024 * 1024), 2),
            "usage_percentage": round((total_usage / storage_limit) * 100, 2),
            "usage_by_type": {
                "images": {
                    "size_bytes": usage_by_type["image"],
                    "size_mb": round(usage_by_type["image"] / (1024 * 1024), 2),
                    "file_count": total_files["image"],
                },
                "videos": {
                    "size_bytes": usage_by_type["video"],
                    "size_mb": round(usage_by_type["video"] / (1024 * 1024), 2),
                    "file_count": total_files["video"],
                },
                "documents": {
                    "size_bytes": usage_by_type["document"],
                    "size_mb": round(usage_by_type["document"] / (1024 * 1024), 2),
                    "file_count": total_files["document"],
                },
            },
            "total_files": sum(total_files.values()),
        }

    except Exception as e:
        logger.error("Failed to get storage info", user_id=current_user.user_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve storage information"
        )
