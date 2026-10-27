"""
Utility functions for PyFlow ETL framework.
Questions 1, 3, 4, 5, 7, 11, 15, 16, 37: Various utilities
"""

import time
import json
import yaml
import logging
import chardet
import functools
from pathlib import Path
from typing import Any, Dict, Generator, List, Callable, TypeVar, cast
from collections import Counter

from pyflow.exceptions import ConfigurationError, RetryExhaustedError

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Question 1: Load configuration from JSON or YAML with error handling.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        ConfigurationError: If file doesn't exist or is invalid
    """
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                config = json.load(f)
            else:
                raise ConfigurationError(f"Unsupported config format: {path.suffix}")
        
        if not isinstance(config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        
        return config
        
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in {config_path}: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load config {config_path}: {e}")


def timing_decorator(func: F) -> F:
    """
    Question 3: Decorator to measure and log function execution time.
    
    Args:
        func: Function to time
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        logger.info(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {e}")
            raise
    
    return cast(F, wrapper)


def read_csv_chunks(file_path: str, chunk_size: int = 10000) -> Generator[str, None, None]:
    """
    Question 4: Generator to read CSV file in chunks.
    Yields rows incrementally without loading entire file into memory.
    
    Args:
        file_path: Path to CSV file
        chunk_size: Number of lines per chunk
        
    Yields:
        Lines from the CSV file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chunk = []
            for line in f:
                chunk.append(line)
                if len(chunk) >= chunk_size:
                    for item in chunk:
                        yield item
                    chunk = []
            
            # Yield remaining lines
            for item in chunk:
                yield item
                
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading CSV chunks from {file_path}: {e}")
        raise


def analyze_email_domains(emails: List[str]) -> Dict[str, int]:
    """
    Question 5: Use list comprehension to extract and count email domains.
    
    Args:
        emails: List of email addresses
        
    Returns:
        Dictionary with domain counts
    """
    # Extract domains using list comprehension
    domains = [email.split('@')[1].lower() for email in emails if '@' in email]
    
    # Count domains using Counter
    return dict(Counter(domains))


def benchmark_list_vs_set(
    sizes: List[int] = [1_000, 5_000, 10_000, 50_000]
) -> Dict[int, Dict[str, float]]:
    """
    Question 11: Compare list vs set membership-testing performance.
    Demonstrates O(n) list lookup vs O(1) set lookup.

    Args:
        sizes: List of dataset sizes to benchmark

    Returns:
        Dictionary mapping each size to its list_ms, set_ms, and speedup
    """
    import random
    random.seed(42)

    results: Dict[int, Dict[str, float]] = {}

    logger.info("Running list vs set benchmark (Question 11)")
    logger.info(f"{'Size':<10} {'List (ms)':<15} {'Set (ms)':<15} {'Speedup':<10}")

    for size in sizes:
        data_list = list(range(size))
        data_set = set(data_list)
        search_values = [random.randint(0, size + 1000) for _ in range(1000)]

        # Benchmark list — O(n)
        start = time.time()
        for v in search_values:
            _ = v in data_list
        list_ms = (time.time() - start) * 1000

        # Benchmark set — O(1)
        start = time.time()
        for v in search_values:
            _ = v in data_set
        set_ms = (time.time() - start) * 1000

        speedup = list_ms / set_ms if set_ms > 0 else float('inf')
        results[size] = {'list_ms': list_ms, 'set_ms': set_ms, 'speedup': speedup}

        logger.info(f"{size:<10} {list_ms:<15.4f} {set_ms:<15.4f} {speedup:<10.2f}x")

    logger.info("Conclusion: Set O(1) lookup is significantly faster than List O(n)")
    return results


def detect_encoding(file_path: str) -> str:
    """
    Question 15: Detect file encoding with fallback behavior.
    
    Args:
        file_path: Path to file
        
    Returns:
        Detected encoding string
    """
    try:
        with open(file_path, 'rb') as f:
            # Read first 100KB for detection
            raw_data = f.read(100000)
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']
            
            logger.info(f"Detected encoding {encoding} with confidence {confidence:.2f} for {file_path}")
            
            # Fallback to utf-8 if confidence is too low
            if encoding is None or confidence < 0.7:
                logger.warning(f"Low confidence or no encoding detected, using UTF-8")
                return 'utf-8'
            
            return encoding
            
    except Exception as e:
        logger.warning(f"Encoding detection failed for {file_path}: {e}. Using UTF-8.")
        return 'utf-8'


def flatten_json(nested_dict: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Question 16: Flatten nested JSON structure.
    
    Args:
        nested_dict: Nested dictionary to flatten
        parent_key: Parent key for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items: List[tuple] = []
    
    for k, v in nested_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_json(item, f"{new_key}{sep}{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}{sep}{i}", item))
        else:
            items.append((new_key, v))
    
    return dict(items)


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Question 37: Retry function with exponential backoff for transient failures.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Result of the function
        
    Raises:
        RetryExhaustedError: If all retries are exhausted
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries} attempts failed")
    
    raise RetryExhaustedError(
        f"Failed after {max_retries} attempts. Last error: {last_exception}"
    )


def setup_logging(
    log_file: str = "logs/pyflow.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """
    Question 36: Setup rotating file handler for logging.
    
    Args:
        log_file: Path to log file
        level: Logging level
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    from logging.handlers import RotatingFileHandler
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers and close them (important on Windows)
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    logger.info("Logging configured successfully")
