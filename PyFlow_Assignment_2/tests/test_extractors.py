"""
Tests for data extractors.
Question 38: Test extractors module.
"""

import pytest
import tempfile
import pandas as pd
from pathlib import Path

from pyflow.extractors import (
    CSVExtractor,
    JSONExtractor,
    ParquetExtractor,
    get_extractor,
)
from pyflow.exceptions import ExtractionError


def test_csv_extractor():
    """Test CSV extraction."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1,col2,col3\n")
        f.write("1,2,3\n")
        f.write("4,5,6\n")
        temp_path = f.name
    
    try:
        extractor = CSVExtractor(temp_path)
        df = extractor.extract()
        
        assert len(df) == 2
        assert list(df.columns) == ['col1', 'col2', 'col3']
        assert df['col1'].tolist() == [1, 4]
    finally:
        Path(temp_path).unlink()


def test_csv_extractor_chunk():
    """Test CSV extraction with chunks."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1,col2\n")
        for i in range(10):
            f.write(f"{i},{i*2}\n")
        temp_path = f.name
    
    try:
        extractor = CSVExtractor(temp_path, chunk_size=3)
        df = extractor.extract()
        
        assert len(df) == 10
    finally:
        Path(temp_path).unlink()


def test_json_extractor():
    """Test JSON extraction."""
    import json
    
    data = [
        {"id": 1, "value": "a"},
        {"id": 2, "value": "b"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        temp_path = f.name
    
    try:
        extractor = JSONExtractor(temp_path)
        df = extractor.extract()
        
        assert len(df) == 2
        assert 'id' in df.columns
        assert 'value' in df.columns
    finally:
        Path(temp_path).unlink()


def test_parquet_extractor():
    """Test Parquet extraction."""
    df_original = pd.DataFrame({
        'col1': [1, 2, 3],
        'col2': ['a', 'b', 'c']
    })
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        temp_path = f.name
        df_original.to_parquet(temp_path)
    
    try:
        extractor = ParquetExtractor(temp_path)
        df = extractor.extract()
        
        assert len(df) == 3
        assert list(df.columns) == ['col1', 'col2']
    finally:
        Path(temp_path).unlink()


def test_extractor_file_not_found():
    """Test extractor with non-existent file."""
    with pytest.raises(ExtractionError):
        extractor = CSVExtractor("nonexistent.csv")


def test_get_extractor_csv():
    """Test extractor factory for CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1\n1\n")
        temp_path = f.name
    
    try:
        extractor = get_extractor(temp_path)
        assert isinstance(extractor, CSVExtractor)
    finally:
        Path(temp_path).unlink()


def test_get_extractor_json():
    """Test extractor factory for JSON."""
    import json
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([{"a": 1}], f)
        temp_path = f.name
    
    try:
        extractor = get_extractor(temp_path)
        assert isinstance(extractor, JSONExtractor)
    finally:
        Path(temp_path).unlink()
