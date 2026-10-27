"""
Tests for data loaders.
Question 38: Test loaders module.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path

from pyflow.loaders import (
    CSVLoader,
    JSONLoader,
    ParquetLoader,
    SQLiteLoader,
    get_loader,
    convert_parquet_to_csv,
)


def test_csv_loader():
    """Test CSV loading."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.csv"
        
        loader = CSVLoader(str(output_path))
        loader.load(df)
        
        assert output_path.exists()
        
        # Verify contents
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 3
        assert list(loaded_df.columns) == ['col1', 'col2']


def test_json_loader():
    """Test JSON loading."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.json"
        
        loader = JSONLoader(str(output_path))
        loader.load(df)
        
        assert output_path.exists()


def test_parquet_loader():
    """Test Parquet loading."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.parquet"
        
        loader = ParquetLoader(str(output_path))
        loader.load(df)
        
        assert output_path.exists()
        
        # Verify contents
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == 3


def test_sqlite_loader():
    """Test SQLite loading."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        loader = SQLiteLoader(str(db_path), table_name='test_table')
        loader.load(df)
        
        assert db_path.exists()
        
        # Verify contents
        import sqlite3
        conn = sqlite3.connect(db_path)
        loaded_df = pd.read_sql_query("SELECT * FROM test_table", conn)
        conn.close()
        
        assert len(loaded_df) == 3


def test_convert_parquet_to_csv():
    """Test Parquet to CSV conversion."""
    df = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "input.parquet"
        csv_path = Path(tmpdir) / "output.csv"
        
        df.to_parquet(parquet_path)
        
        convert_parquet_to_csv(str(parquet_path), str(csv_path))
        
        assert csv_path.exists()
        
        loaded_df = pd.read_csv(csv_path)
        assert len(loaded_df) == 3


def test_get_loader():
    """Test loader factory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.csv"
        
        loader = get_loader(str(output_path))
        
        assert isinstance(loader, CSVLoader)
