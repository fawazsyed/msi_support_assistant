"""Utility functions for MSI AI Assistant."""

from pathlib import Path
import logging
from datetime import datetime
import shutil


def setup_logging(project_root: Path, keep_recent: int = 10) -> logging.Logger:
    """
    Configure logging with file handler and automatic archiving.
    
    Args:
        project_root: Path to project root directory
        keep_recent: Number of recent log files to keep before archiving
        
    Returns:
        Configured logger instance
    """
    # Create logs and archive directories if they don't exist
    logs_dir = project_root / "logs"
    archive_dir = logs_dir / "archive"
    logs_dir.mkdir(exist_ok=True)
    archive_dir.mkdir(exist_ok=True)
    
    # Cleanup old logs before starting new session
    _cleanup_old_logs(logs_dir, archive_dir, keep_recent)
    
    # Configure logging with file handler
    log_filename = f"msi_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = logs_dir / log_filename
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath),  # Write to file
            logging.StreamHandler()              # Also print to console
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging to: {log_filepath}")
    
    return logger


def _cleanup_old_logs(logs_dir: Path, archive_dir: Path, keep_recent: int) -> None:
    """
    Archive old logs, keeping only the most recent ones.
    
    Args:
        logs_dir: Directory containing log files
        archive_dir: Directory for archived logs
        keep_recent: Number of recent log files to keep
    """
    log_files = sorted(
        logs_dir.glob("msi_assistant_*.log"), 
        key=lambda f: f.stat().st_mtime, 
        reverse=True
    )
    
    if len(log_files) > keep_recent:
        for old_log in log_files[keep_recent:]:
            archive_path = archive_dir / old_log.name
            shutil.move(str(old_log), str(archive_path))
            print(f"Archived: {old_log.name}")
