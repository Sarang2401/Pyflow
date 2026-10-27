"""
Data extraction module for various file formats.
Question 31: Extractors for CSV, JSON, Excel, Parquet, and compressed files.
Questions 13, 14, 15, 17, 18, 19: File handling operations.
Bonus Q43: tqdm progress bars on chunk-based loading.
"""

import gzip
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, Iterator

import pandas as pd
from openpyxl import load_workbook
from tqdm import tqdm

from pyflow.exceptions import ExtractionError
from pyflow.utils import detect_encoding

logger = logging.getLogger(__name__)


class BaseExtractor:
    """Base class for all extractors."""
    
    def __init__(self, file_path: str):
        """
        Initialize extractor.
        
        Args:
            file_path: Path to source file
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise ExtractionError(f"File not found: {file_path}")
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data from source.
        
        Returns:
            DataFrame containing extracted data
            
        Raises:
            ExtractionError: If extraction fails
        """
        raise NotImplementedError("Subclasses must implement extract()")


class CSVExtractor(BaseExtractor):
    """
    Question 31a: Extract data from CSV files.
    Question 13: Support for chunk-based processing.
    Question 14: Encoding detection.
    Question 15: Corrupted file handling.
    """
    
    def __init__(
        self,
        file_path: str,
        chunk_size: Optional[int] = None,
        encoding: Optional[str] = None,
        columns: Optional[list] = None,
        sample_size: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Initialize CSV extractor.
        
        Args:
            file_path: Path to CSV file
            chunk_size: Number of rows per chunk (None for full load)
            encoding: File encoding (auto-detected if None)
            columns: List of columns to load (mapped to usecols in pd.read_csv)
            sample_size: Number of rows to randomly sample after reading (None for all)
            **kwargs: Additional pandas read_csv parameters
        """
        super().__init__(file_path)
        self.chunk_size = chunk_size
        self.encoding = encoding
        self.columns = columns
        self.sample_size = sample_size
        self.kwargs = kwargs
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data from CSV file.
        
        Returns:
            DataFrame containing CSV data
        """
        try:
            # Detect encoding if not specified
            if self.encoding is None:
                self.encoding = detect_encoding(str(self.file_path))
            
            logger.info(f"Extracting CSV from {self.file_path} with encoding {self.encoding}")
            
            # Map columns -> usecols (pd.read_csv uses usecols, not columns)
            read_kwargs = dict(self.kwargs)
            if self.columns:
                read_kwargs['usecols'] = self.columns
            
            # Handle chunk-based reading
            if self.chunk_size:
                chunks = []
                # Bonus Q43: tqdm progress bar for chunk-based loading
                reader = pd.read_csv(
                    self.file_path,
                    encoding=self.encoding,
                    chunksize=self.chunk_size,
                    on_bad_lines='warn',  # Question 15: Handle corrupted lines
                    **read_kwargs
                )
                for chunk in tqdm(reader, desc=f"Loading {self.file_path.name}", unit="chunk"):
                    chunks.append(chunk)
                
                df = pd.concat(chunks, ignore_index=True)
                logger.info(f"Loaded {len(chunks)} chunks, total {len(df)} rows")
            else:
                df = pd.read_csv(
                    self.file_path,
                    encoding=self.encoding,
                    on_bad_lines='warn',
                    **read_kwargs
                )
            
            logger.info(f"Successfully extracted {len(df)} rows from CSV")
            
            # Sample if requested (matches ParquetExtractor behaviour)
            if self.sample_size and self.sample_size < len(df):
                logger.info(f"Sampling {self.sample_size} rows from {len(df)} total")
                df = df.sample(n=self.sample_size, random_state=42)
            
            return df
            
        except Exception as e:
            raise ExtractionError(f"Failed to extract CSV from {self.file_path}: {e}")


class JSONExtractor(BaseExtractor):
    """Question 31b: Extract data from JSON files."""
    
    def __init__(self, file_path: str, orient: str = 'records'):
        """
        Initialize JSON extractor.
        
        Args:
            file_path: Path to JSON file
            orient: JSON orientation (records, split, index, columns, values)
        """
        super().__init__(file_path)
        self.orient = orient
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data from JSON file.
        
        Returns:
            DataFrame containing JSON data
        """
        try:
            logger.info(f"Extracting JSON from {self.file_path}")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert to DataFrame based on structure
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ExtractionError(f"Unsupported JSON structure in {self.file_path}")
            
            logger.info(f"Successfully extracted {len(df)} rows from JSON")
            return df
            
        except Exception as e:
            raise ExtractionError(f"Failed to extract JSON from {self.file_path}: {e}")


class ExcelExtractor(BaseExtractor):
    """
    Question 31c: Extract data from Excel files.
    Question 17: Support for merging multiple sheets.
    """
    
    def __init__(
        self,
        file_path: str,
        sheet_name: Union[str, int, None] = 0,
        merge_sheets: bool = False
    ):
        """
        Initialize Excel extractor.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name/index or None for all sheets
            merge_sheets: If True, merge all sheets into one DataFrame
        """
        super().__init__(file_path)
        self.sheet_name = sheet_name
        self.merge_sheets = merge_sheets
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data from Excel file.
        
        Returns:
            DataFrame containing Excel data
        """
        try:
            logger.info(f"Extracting Excel from {self.file_path}")
            
            if self.merge_sheets:
                # Question 17: Merge all sheets
                workbook = load_workbook(self.file_path, read_only=True)
                all_sheets = []
                
                for sheet_name in workbook.sheetnames:
                    df = pd.read_excel(self.file_path, sheet_name=sheet_name)
                    df['source_sheet'] = sheet_name  # Track source
                    all_sheets.append(df)
                
                df = pd.concat(all_sheets, ignore_index=True)
                logger.info(f"Merged {len(all_sheets)} sheets into {len(df)} rows")
            else:
                df = pd.read_excel(self.file_path, sheet_name=self.sheet_name)
                logger.info(f"Extracted {len(df)} rows from Excel")
            
            return df
            
        except Exception as e:
            raise ExtractionError(f"Failed to extract Excel from {self.file_path}: {e}")


class ParquetExtractor(BaseExtractor):
    """Question 31d: Extract data from Parquet files."""
    
    def __init__(self, file_path: str, columns: Optional[list] = None, sample_size: Optional[int] = None, **kwargs: Any):
        """
        Initialize Parquet extractor.
        
        Args:
            file_path: Path to Parquet file
            columns: Columns to load (None for all)
            sample_size: Number of rows to sample (None for all)
            **kwargs: Additional parameters (ignored for Parquet)
        """
        super().__init__(file_path)
        self.columns = columns
        self.sample_size = sample_size
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data from Parquet file.
        
        Returns:
            DataFrame containing Parquet data
        """
        try:
            logger.info(f"Extracting Parquet from {self.file_path}")
            
            df = pd.read_parquet(self.file_path, columns=self.columns)
            
            # Sample if requested
            if self.sample_size and self.sample_size < len(df):
                logger.info(f"Sampling {self.sample_size} rows from {len(df)} total")
                df = df.sample(n=self.sample_size, random_state=42)
            
            logger.info(f"Successfully extracted {len(df)} rows from Parquet")
            return df
            
        except Exception as e:
            raise ExtractionError(f"Failed to extract Parquet from {self.file_path}: {e}")


class CompressedCSVExtractor(BaseExtractor):
    """
    Question 18: Extract data from compressed CSV files (gzip).
    Question 31e: Compressed file support.
    """
    
    def __init__(self, file_path: str, encoding: Optional[str] = None, **kwargs: Any):
        """
        Initialize compressed CSV extractor.
        
        Args:
            file_path: Path to compressed CSV file
            encoding: File encoding (auto-detected if None)
            **kwargs: Additional pandas read_csv parameters
        """
        super().__init__(file_path)
        self.encoding = encoding
        self.kwargs = kwargs
    
    def extract(self) -> pd.DataFrame:
        """
        Extract data from compressed CSV file.
        
        Returns:
            DataFrame containing CSV data
        """
        try:
            logger.info(f"Extracting compressed CSV from {self.file_path}")
            
            # pandas automatically handles gzip compression
            if self.encoding is None:
                # For compressed files, try utf-8 first
                self.encoding = 'utf-8'
            
            df = pd.read_csv(
                self.file_path,
                compression='gzip',
                encoding=self.encoding,
                on_bad_lines='warn',
                **self.kwargs
            )
            
            logger.info(f"Successfully extracted {len(df)} rows from compressed CSV")
            return df
            
        except Exception as e:
            raise ExtractionError(f"Failed to extract compressed CSV from {self.file_path}: {e}")


def get_extractor(
    file_path: str,
    file_type: Optional[str] = None,
    **kwargs: Any
) -> BaseExtractor:
    """
    Factory function to get appropriate extractor based on file type.
    
    Args:
        file_path: Path to file
        file_type: File type override (csv, json, excel, parquet, gzip)
        **kwargs: Additional extractor parameters
        
    Returns:
        Appropriate extractor instance
        
    Raises:
        ExtractionError: If file type is unsupported
    """
    path = Path(file_path)
    
    # Determine file type
    if file_type is None:
        file_type = path.suffix.lower().lstrip('.')
    
    # Handle compressed files
    if file_type == 'gz' or path.suffix == '.gz':
        return CompressedCSVExtractor(file_path, **kwargs)
    
    # Map file types to extractors
    extractors = {
        'csv': CSVExtractor,
        'json': JSONExtractor,
        'xlsx': ExcelExtractor,
        'xls': ExcelExtractor,
        'parquet': ParquetExtractor,
    }
    
    extractor_class = extractors.get(file_type)
    
    if extractor_class is None:
        raise ExtractionError(f"Unsupported file type: {file_type}")
    
    return extractor_class(file_path, **kwargs)
