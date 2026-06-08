from __future__ import annotations
import os
import time
from datetime import datetime, timezone, timedelta
from celery.utils.log import get_task_logger
from tuned.celery_app import celery_app
from tuned.extensions import db
from tuned.models.media import MediaAsset
from flask import current_app

logger = get_task_logger(__name__)


@celery_app.task(
    name="tuned.tasks.media_tasks.cleanup_deleted_media",
    queue="celery"
)
def cleanup_deleted_media() -> None:
    logger.info("[cleanup_deleted_media] Starting cleanup of deleted media...")
    try:
        # 30 days threshold
        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Find all soft-deleted assets older than 30 days
        deleted_assets = db.session.query(MediaAsset).filter(
            MediaAsset.is_deleted == True,
            MediaAsset.deleted_at <= threshold
        ).all()
        
        count = 0
        upload_root = current_app.config.get("UPLOAD_ROOT", "")
        if not upload_root:
            logger.warning("[cleanup_deleted_media] UPLOAD_ROOT not configured, skipping cleanup of deleted media")
            return
        for asset in deleted_assets:
            physical_path = os.path.join(upload_root, asset.storage_path)
            if os.path.exists(physical_path):
                try:
                    os.remove(physical_path)
                    logger.info("[cleanup_deleted_media] Deleted file: %s", physical_path)
                except Exception as file_exc:
                    logger.error("[cleanup_deleted_media] Failed to delete file %s: %r", physical_path, file_exc)
            
            # Hard delete from DB
            db.session.delete(asset)
            count += 1
            
        db.session.commit()
        logger.info("[cleanup_deleted_media] Hard deleted %d media records.", count)
        
        # Clean up temp files older than 24 hours
        temp_dir = os.path.join(upload_root, "temp")
        if os.path.exists(temp_dir):
            now_time = time.time()
            temp_count = 0
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                if os.path.isfile(file_path):
                    # Check age
                    stat = os.stat(file_path)
                    if now_time - stat.st_mtime > 86400:  # 24 hours
                        try:
                            os.remove(file_path)
                            temp_count += 1
                        except Exception as temp_exc:
                            logger.error("[cleanup_deleted_media] Failed to delete temp file %s: %r", file_path, temp_exc)
            logger.info("[cleanup_deleted_media] Cleaned up %d temp zip files.", temp_count)
            
    except Exception as exc:
        db.session.rollback()
        logger.error("[cleanup_deleted_media] Task failed: %r", exc)
