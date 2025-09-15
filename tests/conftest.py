"""
Pytest configuration and fixtures for Where Was Eye tests.

This file provides shared fixtures and configuration for all tests.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import Mock, patch

from where_was_eye.timeline_db import MyTimelineDB


@pytest.fixture
def mock_timeline_data():
    """Fixture providing mock timeline data for testing."""
    return [
        {
            "startTime": "2024-08-20T15:30:00Z",
            "endTime": "2024-08-20T16:30:00Z",
            "visit": {
                "topCandidate": {
                    "placeLocation": {
                        "latitude": 40.7128,
                        "longitude": -74.0060
                    }
                }
            }
        },
        {
            "startTime": "2024-08-20T17:00:00Z",
            "endTime": "2024-08-20T18:00:00Z",
            "activity": {
                "start": {
                    "latitude": 40.7580,
                    "longitude": -73.9855
                }
            }
        }
    ]


@pytest.fixture
def temp_timeline_file(mock_timeline_data):
    """Fixture creating a temporary timeline JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_timeline_data, f)
        temp_file = f.name
    
    yield temp_file
    
    # Clean up
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def timeline_db(temp_timeline_file):
    """Fixture providing a pre-initialized timeline database."""
    return MyTimelineDB(temp_timeline_file)


@pytest.fixture
def mock_ai_client():
    """Fixture providing a mock AI client for testing."""
    with patch('where_was_eye.agent.OpenAIClient') as mock_client:
        yield mock_client


@pytest.fixture
def mock_ollama_client():
    """Fixture providing a mock Ollama client for testing."""
    with patch('where_was_eye.agent.OllamaClient') as mock_client:
        yield mock_client


@pytest.fixture(autouse=True)
def cleanup_cache():
    """Clean up cache files after tests."""
    yield
    # Clean up any cache directories that might have been created
    cache_dirs = [".timeline_cache", ".timeline_cache_test"]
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir) and os.path.isdir(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)