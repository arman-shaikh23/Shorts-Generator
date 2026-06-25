import logging
import time
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _slugify(value: str) -> str:
    if not value:
        return "default"
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value).strip("._") or "default"


def upload_output_video_to_blob(
    local_path: str,
    project_id: str,
    style: str,
    variation_index: int = 0,
) -> Optional[str]:
    """
    Upload a rendered output video to Azure Blob Storage and return the blob URL.
    Returns None when blob output is disabled or upload fails.
    """
    settings = get_settings()
    if not settings.ENABLE_AZURE_BLOB_OUTPUT:
        return None

    connection_string = (settings.AZURE_STORAGE_CONNECTION_STRING or "").strip()
    if not connection_string:
        logger.warning("[BLOB] ENABLE_AZURE_BLOB_OUTPUT=true but AZURE_STORAGE_CONNECTION_STRING is empty.")
        return None

    container_name = (settings.AZURE_BLOB_OUTPUT_CONTAINER or "reels").strip().lower() or "reels"

    try:
        from azure.core.exceptions import ResourceExistsError
        from azure.storage.blob import BlobServiceClient, ContentSettings
    except Exception as exc:
        logger.warning("[BLOB] Azure Blob SDK is unavailable: %s", exc)
        return None

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        try:
            container_client.create_container(public_access="blob")
        except ResourceExistsError:
            pass

        file_name = Path(local_path).name
        style_slug = _slugify(style)
        blob_name = f"{project_id}/{style_slug}/{int(time.time() * 1000)}_{variation_index}_{file_name}"
        blob_client = container_client.get_blob_client(blob_name)

        with open(local_path, "rb") as fh:
            blob_client.upload_blob(
                fh,
                overwrite=True,
                content_settings=ContentSettings(content_type="video/mp4"),
            )

        return blob_client.url
    except Exception as exc:
        logger.exception("[BLOB] Failed to upload output '%s': %s", local_path, exc)
        return None
