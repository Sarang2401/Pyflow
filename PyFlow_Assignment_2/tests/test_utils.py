"""
Tests for utility functions.
Question 38: Test utils module.
"""

import pytest
import json
import yaml
import tempfile
from pathlib import Path

from pyflow.utils import (
    load_config,
    timing_decorator,
    read_csv_chunks,
    analyze_email_domains,
    detect_encoding,
    flatten_json,
    retry_with_backoff,
)
from pyflow.exceptions import ConfigurationError, RetryExhaustedError


def test_load_config_json():
    """Test loading JSON configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {"key": "value", "number": 42}
        json.dump(config, f)
        temp_path = f.name
    
    try:
        loaded = load_config(temp_path)
        assert loaded == config
    finally:
        Path(temp_path).unlink()


def test_load_config_yaml():
    """Test loading YAML configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {"key": "value", "list": [1, 2, 3]}
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        loaded = load_config(temp_path)
        assert loaded == config
    finally:
        Path(temp_path).unlink()


def test_load_config_invalid_file():
    """Test loading non-existent configuration."""
    with pytest.raises(ConfigurationError):
        load_config("nonexistent.json")


def test_load_config_invalid_json():
    """Test loading invalid JSON."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json")
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigurationError):
            load_config(temp_path)
    finally:
        Path(temp_path).unlink()


def test_timing_decorator():
    """Test timing decorator."""
    @timing_decorator
    def sample_function():
        return "done"
    
    result = sample_function()
    assert result == "done"


def test_read_csv_chunks():
    """Test CSV chunk reading."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("col1,col2\n")
        for i in range(10):
            f.write(f"{i},{i*2}\n")
        temp_path = f.name
    
    try:
        chunks = list(read_csv_chunks(temp_path, chunk_size=5))
        assert len(chunks) == 11  # header + 10 rows
    finally:
        Path(temp_path).unlink()


def test_analyze_email_domains():
    """Test email domain analysis."""
    emails = [
        "user1@example.com",
        "user2@example.com",
        "user3@test.org",
        "invalid-email",
        "user4@test.org"
    ]
    
    domains = analyze_email_domains(emails)
    
    assert domains["example.com"] == 2
    assert domains["test.org"] == 2
    assert len(domains) == 2


def test_flatten_json():
    """Test JSON flattening."""
    nested = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": 3
            }
        },
        "f": [1, 2, {"g": 4}]
    }
    
    flat = flatten_json(nested)
    
    assert flat["a"] == 1
    assert flat["b_c"] == 2
    assert flat["b_d_e"] == 3
    assert flat["f_0"] == 1
    assert flat["f_2_g"] == 4


def test_retry_success():
    """Test retry with successful function."""
    attempts = []
    
    def successful_func():
        attempts.append(1)
        return "success"
    
    result = retry_with_backoff(successful_func, max_retries=3)
    
    assert result == "success"
    assert len(attempts) == 1


def test_retry_eventual_success():
    """Test retry with eventual success."""
    attempts = []
    
    def flaky_func():
        attempts.append(1)
        if len(attempts) < 3:
            raise ValueError("Transient error")
        return "success"
    
    result = retry_with_backoff(flaky_func, max_retries=5, initial_delay=0.1)
    
    assert result == "success"
    assert len(attempts) == 3


def test_retry_exhausted():
    """Test retry with all attempts failed."""
    def failing_func():
        raise ValueError("Persistent error")
    
    with pytest.raises(RetryExhaustedError):
        retry_with_backoff(failing_func, max_retries=3, initial_delay=0.1)
