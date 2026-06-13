import asyncio
import logging
from bson import ObjectId
from app.core.database import get_db
from services.video import download_video, create_preview

logger = logging.getLogger(__name__)

async def process_pending_uploads():
    """Background task to process any PENDING uploads."""
    db = get_db()
    
    while True:
        try:
            # Find one pending upload
            upload = await db.uploads.find_one({"status": "PENDING"})
            
            if not upload:
                await asyncio.sleep(5)  # No pending uploads, wait and poll
                continue
                
            upload_id = str(upload["_id"])
            project_id = upload["projectId"]
            url = upload["originalUrl"]
            filename = upload["filename"]
            
            logger.info(f"Processing upload {upload_id} for project {project_id}")
            
            # Mark as processing
            await db.uploads.update_one(
                {"_id": ObjectId(upload_id)},
                {"$set": {"status": "PROCESSING"}}
            )
            
            # 1. Download Video (Skip if local upload)
            local_path = upload.get("localPath")
            if not local_path or not url.startswith("local://"):
                local_path = await download_video(url, filename, project_id)
            
            # Check if user cancelled/deleted the clip during download
            check = await db.uploads.find_one({"_id": ObjectId(upload_id)})
            if not check:
                logger.info(f"Upload {upload_id} was cancelled by user. Aborting.")
                continue

            # 2. Create Preview
            preview_path = await create_preview(local_path, project_id)
            
            # Check again before final save
            check = await db.uploads.find_one({"_id": ObjectId(upload_id)})
            if not check:
                logger.info(f"Upload {upload_id} was cancelled by user. Aborting.")
                continue

            # 3. Update DB
            await db.uploads.update_one(
                {"_id": ObjectId(upload_id)},
                {"$set": {
                    "status": "PROCESSED",
                    "localPath": local_path,
                    "previewPath": preview_path
                }}
            )
            
            logger.info(f"Successfully processed upload {upload_id}")
            
        except Exception as e:
            logger.error(f"Error processing upload: {e}")
            if 'upload_id' in locals():
                try:
                    await db.uploads.update_one(
                        {"_id": ObjectId(upload_id)},
                        {"$set": {"status": "FAILED", "error": str(e)}}
                    )
                except Exception as db_e:
                    logger.error(f"Failed to update error status: {db_e}")
            await asyncio.sleep(5)

# We will start this task in main.py startup event
