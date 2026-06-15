import asyncio
import logging
from bson import ObjectId
from app.core.database import get_db
from services.video import download_video, create_preview
from services.deduplication import analyze_duplicate

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
                
            # --- PRE-PROCESS: 3-STAGE DUPLICATE DETECTION ---
            # Get all existing PROCESSED or PROCESSING uploads for this project (excluding self)
            cursor = db.uploads.find({
                "projectId": project_id, 
                "_id": {"$ne": ObjectId(upload_id)},
                "status": {"$in": ["PROCESSED", "PROCESSING", "DUPLICATE"]}
            })
            existing_files = await cursor.to_list(length=100)
            
            # Offload heavy CPU bound duplicate analysis to a thread
            is_dup, reason, dup_data = await asyncio.to_thread(analyze_duplicate, local_path, existing_files)
            
            if is_dup:
                logger.info(f"Duplicate detected for {upload_id}: {reason}")
                await db.uploads.update_one(
                    {"_id": ObjectId(upload_id)},
                    {"$set": {
                        "status": "DUPLICATE",
                        "duplicateReason": reason,
                        "localPath": local_path,
                        "fileHash": dup_data.get("fileHash"),
                        "pHashes": dup_data.get("pHashes")
                    }}
                )
                continue # Skip preview generation and stop processing this clip

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
                    "previewPath": preview_path,
                    "fileHash": dup_data.get("fileHash"),
                    "pHashes": dup_data.get("pHashes")
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
