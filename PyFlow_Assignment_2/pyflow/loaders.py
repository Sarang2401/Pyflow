"""
Data loading module for various output formats.
Question 33: Loaders for CSV, JSON, Excel, Parquet, and SQLite.
Question 30: Export to multiple formats.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from pyflow.database import DatabaseConnection
from pyflow.exceptions import LoadingError

logger = logging.getLogger(__name__)


class BaseLoader:
    """Base class for all loaders."""
    
    def __init__(self, output_path: str):
        """
        Initialize loader.
        
        Args:
            output_path: Path to output file/directory
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def load(self, df: pd.DataFrame) -> None:
        """
        Load data to destination.
        
        Args:
            df: DataFrame to load
            
        Raises:
            LoadingError: If loading fails
        """
        raise NotImplementedError("Subclasses must implement load()")


class CSVLoader(BaseLoader):
    """Question 30a & 33a: Load data to CSV files."""
    
    def __init__(self, output_path: str, **kwargs: Any):
        """
        Initialize CSV loader.
        
        Args:
            output_path: Path to output CSV file
            **kwargs: Additional pandas to_csv parameters
        """
        super().__init__(output_path)
        self.kwargs = kwargs
    
    def load(self, df: pd.DataFrame) -> None:
        """Load data to CSV file."""
        try:
            logger.info(f"Loading {len(df)} rows to CSV: {self.output_path}")
            
            df.to_csv(self.output_path, index=False, **self.kwargs)
            
            logger.info(f"Successfully loaded to {self.output_path}")
            
        except Exception as e:
            raise LoadingError(f"Failed to load CSV to {self.output_path}: {e}")


class JSONLoader(BaseLoader):
    """Question 30b & 33b: Load data to JSON files."""
    
    def __init__(self, output_path: str, orient: str = 'records', **kwargs: Any):
        """
        Initialize JSON loader.
        
        Args:
            output_path: Path to output JSON file
            orient: JSON orientation
            **kwargs: Additional pandas to_json parameters
        """
        super().__init__(output_path)
        self.orient = orient
        self.kwargs = kwargs
    
    def load(self, df: pd.DataFrame) -> None:
        """Load data to JSON file."""
        try:
            logger.info(f"Loading {len(df)} rows to JSON: {self.output_path}")
            
            df.to_json(self.output_path, orient=self.orient, **self.kwargs)
            
            logger.info(f"Successfully loaded to {self.output_path}")
            
        except Exception as e:
            raise LoadingError(f"Failed to load JSON to {self.output_path}: {e}")


class ExcelLoader(BaseLoader):
    """Question 30c & 33c: Load data to Excel files."""
    
    def __init__(self, output_path: str, sheet_name: str = 'Sheet1', **kwargs: Any):
        """
        Initialize Excel loader.
        
        Args:
            output_path: Path to output Excel file
            sheet_name: Name of the sheet
            **kwargs: Additional pandas to_excel parameters
        """
        super().__init__(output_path)
        self.sheet_name = sheet_name
        self.kwargs = kwargs
    
    def load(self, df: pd.DataFrame) -> None:
        """Load data to Excel file."""
        try:
            logger.info(f"Loading {len(df)} rows to Excel: {self.output_path}")
            
            df.to_excel(self.output_path, sheet_name=self.sheet_name, index=False, **self.kwargs)
            
            logger.info(f"Successfully loaded to {self.output_path}")
            
        except Exception as e:
            raise LoadingError(f"Failed to load Excel to {self.output_path}: {e}")


class ParquetLoader(BaseLoader):
    """Question 30d & 33d: Load data to Parquet files."""
    
    def __init__(self, output_path: str, **kwargs: Any):
        """
        Initialize Parquet loader.
        
        Args:
            output_path: Path to output Parquet file
            **kwargs: Additional pandas to_parquet parameters
        """
        super().__init__(output_path)
        self.kwargs = kwargs
    
    def load(self, df: pd.DataFrame) -> None:
        """Load data to Parquet file."""
        try:
            logger.info(f"Loading {len(df)} rows to Parquet: {self.output_path}")
            
            df.to_parquet(self.output_path, index=False, **self.kwargs)
            
            logger.info(f"Successfully loaded to {self.output_path}")
            
        except Exception as e:
            raise LoadingError(f"Failed to load Parquet to {self.output_path}: {e}")


class SQLiteLoader:
    """Question 33e: Load data to SQLite database."""
    
    def __init__(
        self,
        db_path: str = "data/output/pyflow.db",
        table_name: str = "trips",
        if_exists: str = 'replace'
    ):
        """
        Initialize SQLite loader.
        
        Args:
            db_path: Path to SQLite database
            table_name: Name of table to load data into
            if_exists: What to do if table exists ('fail', 'replace', 'append')
        """
        self.db_path = db_path
        self.table_name = table_name
        self.if_exists = if_exists
    
    def load(self, df: pd.DataFrame) -> None:
        """
        Load data to SQLite database.
        
        Args:
            df: DataFrame to load
            
        Raises:
            LoadingError: If loading fails
        """
        try:
            import sqlite3
            logger.info(f"Loading {len(df)} rows to SQLite table '{self.table_name}'")
            
            # Ensure output directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            try:
                df.to_sql(self.table_name, conn, if_exists=self.if_exists, index=False)
                conn.commit()
            finally:
                conn.close()
            
            logger.info(f"Successfully loaded {len(df)} rows to {self.table_name}")
            
        except Exception as e:
            raise LoadingError(f"Failed to load to SQLite: {e}")
    
    def load_with_validation(
        self,
        df: pd.DataFrame,
        schema: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Load data to SQLite with schema validation.
        
        Args:
            df: DataFrame to load
            schema: Optional schema definition
        """
        try:
            with DatabaseConnection(self.db_path) as db:
                # Create table if schema provided
                if schema:
                    schema_str = ', '.join([f"{col} {dtype}" for col, dtype in schema.items()])
                    db.create_table(self.table_name, schema_str, drop_if_exists=True)
                
                # Convert DataFrame to list of tuples
                columns = df.columns.tolist()
                values = [tuple(row) for row in df.itertuples(index=False, name=None)]
                
                # Build parameterized INSERT query
                placeholders = ','.join(['?' for _ in columns])
                insert_query = f"INSERT INTO {self.table_name} ({','.join(columns)}) VALUES ({placeholders})"
                
                # Batch insert
                db.executemany(insert_query, values)
                
                logger.info(f"Loaded {len(df)} rows to {self.table_name} with parameterized query")
                
        except Exception as e:
            raise LoadingError(f"Failed to load to SQLite with validation: {e}")


def convert_parquet_to_csv(parquet_path: str, csv_path: str) -> None:
    """
    Question 19: Convert Parquet file to CSV.
    
    Args:
        parquet_path: Path to input Parquet file
        csv_path: Path to output CSV file
        
    Raises:
        LoadingError: If conversion fails
    """
    try:
        logger.info(f"Converting Parquet to CSV: {parquet_path} -> {csv_path}")
        
        # Read parquet
        df = pd.read_parquet(parquet_path)
        
        # Write CSV
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Successfully converted {len(df)} rows to CSV")
        
    except Exception as e:
        raise LoadingError(f"Failed to convert Parquet to CSV: {e}")


def get_loader(
    output_path: str,
    format_type: Optional[str] = None,
    **kwargs: Any
) -> BaseLoader:
    """
    Factory function to get appropriate loader based on format.
    
    Args:
        output_path: Path to output file
        format_type: Format override (csv, json, excel, parquet)
        **kwargs: Additional loader parameters
        
    Returns:
        Appropriate loader instance
        
    Raises:
        LoadingError: If format is unsupported
    """
    path = Path(output_path)
    
    # Determine format
    if format_type is None:
        format_type = path.suffix.lower().lstrip('.')
    
    # Map formats to loaders
    loaders = {
        'csv': CSVLoader,
        'json': JSONLoader,
        'xlsx': ExcelLoader,
        'xls': ExcelLoader,
        'parquet': ParquetLoader,
    }
    
    loader_class = loaders.get(format_type)
    
    if loader_class is None:
        raise LoadingError(f"Unsupported output format: {format_type}")
    
    return loader_class(output_path, **kwargs)
