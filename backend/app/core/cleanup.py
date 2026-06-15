import asyncio
import os
import time
import shutil
import logging

logger = logging.getLogger(__name__)

async def run_daily_cleanup():
    """Background task to clean up old temp files and orphaned artifacts every 24 hours."""
    while True:
        try:
            logger.info("Starting Daily Storage Cleanup Sweep...")
            
            # The base data directory where all projects exist
            base_data_dir = "data"
            if not os.path.exists(base_data_dir):
                await asyncio.sleep(86400) # Sleep 24 hours
                continue
                
            now = time.time()
            deleted_files = 0
            recovered_bytes = 0
            
            # Look inside every project directory
            for project_dir in os.listdir(base_data_dir):
                proj_path = os.path.join(base_data_dir, project_dir)
                
                # Skip the library directory (user's music)
                if project_dir == "library" or not os.path.isdir(proj_path):
                    continue
                    
                # Clean the outputs folder (look for old clip_*.mp4 files that the aggressive cleaner might have missed if the server crashed)
                outputs_path = os.path.join(proj_path, "outputs")
                if os.path.exists(outputs_path):
                    for file in os.listdir(outputs_path):
                        if file.startswith("clip_") and file.endswith(".mp4"):
                            file_path = os.path.join(outputs_path, file)
                            # Only delete if older than 24 hours to prevent deleting currently generating files
                            if os.path.getmtime(file_path) < now - 86400:
                                try:
                                    size = os.path.getsize(file_path)
                                    os.remove(file_path)
                                    deleted_files += 1
                                    recovered_bytes += size
                                except Exception as e:
                                    logger.error(f"Failed to delete orphaned temp file {file_path}: {e}")

                # Clean the raw/temp downloads if needed
                raw_path = os.path.join(proj_path, "raw")
                if os.path.exists(raw_path):
                    # We keep raw files if they are needed, but if there's a temp directory, we can clear it.
                    pass
                    
            if deleted_files > 0:
                logger.info(f"Daily Cleanup Complete. Purged {deleted_files} orphaned files. Recovered {recovered_bytes / (1024*1024):.2f} MB of storage.")
            else:
                logger.info("Daily Cleanup Complete. Storage is already optimized.")
                
        except Exception as e:
            logger.error(f"Daily cleanup encountered an error: {e}")
            
        # Run exactly once every 24 hours
        await asyncio.sleep(86400)
