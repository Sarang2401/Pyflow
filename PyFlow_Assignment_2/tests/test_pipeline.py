"""
Tests for pipeline orchestration.
Question 38: Test pipeline module.
"""

import pytest
import tempfile
import pandas as pd
import json
from pathlib import Path

from pyflow.pipeline import ETLPipeline
from pyflow.exceptions import PyFlowException


def create_test_config(data_path: str, output_dir: str) -> str:
    """Create a minimal test configuration."""
    config = {
        "pipeline": {
            "name": "Test Pipeline",
            "version": "1.0.0",
            "description": "Test configuration"
        },
        "extraction": {
            "source_file": data_path,
            "file_type": "csv"
        },
        "transformation": {
            "missing_values": {
                "strategy": "drop"
            },
            "duplicates": {
                "enabled": True,
                "keep": "first"
            },
            "datetime_columns": [],
            "filters": {}
        },
        "aggregation": {},
        "loading": {
            "outputs": {
                "processed_csv": str(Path(output_dir) / "output.csv")
            },
            "database": {
                "enabled": False
            }
        },
        "validation": {
            "required_columns": ["col1"],
            "non_null_columns": [],
            "value_ranges": {}
        },
        "logging": {
            "level": "INFO",
            "file": str(Path(output_dir) / "test.log")
        }
    }
    
    config_path = Path(output_dir) / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    return str(config_path)


def test_pipeline_initialization():
    """Test pipeline initialization."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        # Create dummy data
        data_path = Path(tmpdir) / "data.csv"
        pd.DataFrame({'col1': [1, 2, 3]}).to_csv(data_path, index=False)
        
        # Create config
        config_path = create_test_config(str(data_path), tmpdir)
        
        # Initialize pipeline
        pipeline = ETLPipeline(config_path)
        
        assert pipeline.config is not None
        assert pipeline.df is None


def test_pipeline_extract():
    """Test pipeline extraction phase."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        # Create dummy data
        data_path = Path(tmpdir) / "data.csv"
        pd.DataFrame({'col1': [1, 2, 3]}).to_csv(data_path, index=False)
        
        # Create config
        config_path = create_test_config(str(data_path), tmpdir)
        
        # Run extraction
        pipeline = ETLPipeline(config_path)
        df = pipeline.extract()
        
        assert df is not None
        assert len(df) == 3
        assert 'initial_rows' in pipeline.stats


def test_pipeline_missing_data():
    """Test pipeline with missing source file."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        # Create config with non-existent data file
        config_path = create_test_config("nonexistent.csv", tmpdir)
        
        pipeline = ETLPipeline(config_path)
        
        with pytest.raises(Exception):
            pipeline.extract()
