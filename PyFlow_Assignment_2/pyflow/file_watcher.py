"""
File system watcher for automated file processing.
Question 20: File watcher that processes new supported files.
"""

import time
import logging
from pathlib import Path
from typing import Set, Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from pyflow.extractors import get_extractor
from pyflow.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class FileProcessorHandler(FileSystemEventHandler):
    """
    Question 20: Event handler for processing new files.
    Monitors directory for new files and processes supported formats.
    """
    
    SUPPORTED_EXTENSIONS = {'.csv', '.json', '.xlsx', '.xls', '.parquet', '.gz'}
    
    def __init__(
        self,
        output_dir: str,
        processor_callback: Optional[Callable] = None
    ):
        """
        Initialize file processor handler.
        
        Args:
            output_dir: Directory to save processed files
            processor_callback: Optional callback function for custom processing
        """
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.processed_files: Set[str] = set()
        self.processor_callback = processor_callback
    
    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.debug(f"Ignoring unsupported file: {file_path}")
            return
        
        # Check if already processed
        if str(file_path) in self.processed_files:
            logger.debug(f"File already processed: {file_path}")
            return
        
        logger.info(f"New file detected: {file_path}")
        
        # Small delay to ensure file is fully written
        time.sleep(0.5)
        
        # Process file
        self._process_file(file_path)
    
    def _process_file(self, file_path: Path) -> None:
        """
        Process a detected file.
        
        Args:
            file_path: Path to file to process
        """
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Extract data
            extractor = get_extractor(str(file_path))
            df = extractor.extract()
            
            # Use custom callback if provided
            if self.processor_callback:
                df = self.processor_callback(df)
            
            # Save processed data
            output_file = self.output_dir / f"processed_{file_path.stem}.csv"
            df.to_csv(output_file, index=False)
            
            logger.info(f"Processed {len(df)} rows from {file_path}")
            logger.info(f"Saved to {output_file}")
            
            # Mark as processed
            self.processed_files.add(str(file_path))
            
        except ExtractionError as e:
            logger.error(f"Failed to extract {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")


class FileWatcher:
    """
    Question 20: File watcher with safe shutdown.
    Monitors directory for new files and processes them automatically.
    """
    
    def __init__(
        self,
        watch_dir: str,
        output_dir: str,
        processor_callback: Optional[Callable] = None
    ):
        """
        Initialize file watcher.
        
        Args:
            watch_dir: Directory to watch for new files
            output_dir: Directory to save processed files
            processor_callback: Optional callback for custom processing
        """
        self.watch_dir = Path(watch_dir)
        self.output_dir = Path(output_dir)
        
        if not self.watch_dir.exists():
            raise ValueError(f"Watch directory does not exist: {watch_dir}")
        
        self.event_handler = FileProcessorHandler(output_dir, processor_callback)
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.watch_dir),
            recursive=False
        )
        
        logger.info(f"File watcher initialized: {watch_dir} -> {output_dir}")
    
    def start(self, duration: Optional[float] = None) -> None:
        """
        Start watching for files.
        
        Args:
            duration: How long to watch (seconds). None for indefinite.
        """
        try:
            logger.info(f"Starting file watcher on {self.watch_dir}")
            self.observer.start()
            
            if duration:
                logger.info(f"Watching for {duration} seconds...")
                time.sleep(duration)
                self.stop()
            else:
                logger.info("Watching indefinitely. Press Ctrl+C to stop.")
                while self.observer.is_alive():
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Received stop signal")
            self.stop()
    
    def stop(self) -> None:
        """Stop watching for files."""
        logger.info("Stopping file watcher...")
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped")


def demo_file_watcher(watch_dir: str = "data/samples", duration: float = 10.0) -> None:
    """
    Demonstration of file watcher functionality.
    
    Args:
        watch_dir: Directory to watch
        duration: How long to watch (seconds)
    """
    from pyflow.utils import setup_logging
    
    setup_logging()
    
    logger.info("=" * 80)
    logger.info("FILE WATCHER DEMO")
    logger.info("=" * 80)
    
    watcher = FileWatcher(
        watch_dir=watch_dir,
        output_dir="data/processed"
    )
    
    watcher.start(duration=duration)
    
    logger.info(f"Processed {len(watcher.event_handler.processed_files)} files")
