"""File System Utilities

This module contains helper functions for file and directory operations.
"""

import os
import shutil

import structlog

logger = structlog.get_logger(__name__)


def clear_temp_uploads(temp_dir: str):
    """Clears all files and subdirectories from a given temporary directory.

    Args:
        temp_dir (str): The absolute path to the temporary directory to clear.

    """
    if not os.path.exists(temp_dir):
        logger.warning(
            "Temporary directory does not exist. Skipping cleanup.",
            path=temp_dir)
        return

    if not os.path.isdir(temp_dir):
        logger.error("Path is not a directory. Aborting cleanup.", path=temp_dir)
        return

    logger.info("Clearing temporary upload directory", path=temp_dir)
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            logger.info("Successfully removed temporary file/directory", path=file_path)
        except (OSError, PermissionError) as e:
            logger.exception(
                "Failed to delete temporary file",
                path=file_path,
                error=str(e))
