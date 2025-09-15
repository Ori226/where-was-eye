"""
Tests for the Google Timeline Database Parser.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

from src.where_was_eye.timeline_db import MyTimelineDB, extract_interval, parse_dt_loose


def create_test_timeline_file(file_path: str) -> None:
    """Create a minimal test timeline JSON file."""
    test_data = [
        {
            "visit": {
                "topCandidate": {
                    "placeLocation": {
                        "latitude": 37.7749,
                        "longitude": -122.4194
                    }
                }
            },
            "startTime": "2021-01-15T15:30:00Z",
            "endTime": "2021-01-15T16:30:00Z"
        },
        {
            "activity": {
                "start": {
                    "latitude": 37.7849,
                    "longitude": -122.4294
                },
                "end": {
                    "latitude": 37.7949,
                    "longitude": -122.4394
                }
            },
            "startTime": "2021-01-15T17:30:00Z",
            "endTime": "2021-01-15T18:30:00Z"
        },
                {
            "activity": {
                "start": {
                    "latitude": 37.7849,
                    "longitude": -122.4294
                },
                "end": {
                    "latitude": 37.7949,
                    "longitude": -122.4394
                }
            },
            "startTime": "2021-01-16T17:30:00Z",
            "endTime": "2021-01-16T18:30:00Z"
        },
    ]
    
    with open(file_path, 'w') as f:
        json.dump(test_data, f)


def test_extract_interval():
    """Test interval extraction from various text formats."""
    # Test with proper JSON
    json_text = '{"startTime": "2021-01-15T15:30:00Z", "endTime": "2021-01-15T16:30:00Z"}'
    start_dt, end_dt, meta = extract_interval(json_text)
    assert start_dt is not None
    assert end_dt is not None
    assert meta['start_raw'] == "2021-01-15T15:30:00Z"
    assert meta['end_raw'] == "2021-01-15T16:30:00Z"

    # Test with single quotes
    single_quote_text = "{'start_time': '2021-01-15T15:30:00Z', 'end_time': '2021-01-15T16:30:00Z'}"
    start_dt, end_dt, meta = extract_interval(single_quote_text)
    assert start_dt is not None
    assert end_dt is not None

    # Test with ISO timestamps in text
    text_with_timestamps = "Some text with 2021-01-15T15:30:00Z and 2021-01-15T16:30:00Z timestamps"
    start_dt, end_dt, meta = extract_interval(text_with_timestamps)
    assert start_dt is not None
    assert end_dt is not None


def test_parse_dt_loose():
    """Test loose datetime parsing."""
    # Test ISO format with Z
    dt = parse_dt_loose("2021-01-15T15:30:00Z")
    assert dt is not None
    assert dt.year == 2021
    assert dt.month == 1
    assert dt.day == 15
    assert dt.hour == 15
    assert dt.minute == 30

    # Test ISO format with timezone offset
    dt = parse_dt_loose("2021-01-15T15:30:00+00:00")
    assert dt is not None

    # Test invalid format
    dt = parse_dt_loose("invalid-date")
    assert dt is None


def test_timeline_db_initialization():
    """Test timeline database initialization with test data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        create_test_timeline_file(f.name)
        temp_file = f.name

    try:
        # Test initialization
        db = MyTimelineDB(temp_file)
        assert db._time_idx is not None
        assert db._all_data is not None
        assert len(db._time_idx) == 3  # Should have 3 intervals

        # Test cache creation
        cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache")
        assert os.path.exists(os.path.join(cache_dir, "intervals.npz"))
        assert os.path.exists(os.path.join(cache_dir, "all_data.pkl"))
        assert os.path.exists(os.path.join(cache_dir, "source_hash.txt"))

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache")
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)


def test_get_location_at_time():
    """Test location retrieval at specific times."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        create_test_timeline_file(f.name)
        temp_file = f.name

    try:
        db = MyTimelineDB(temp_file)

        # Test within first interval
        location = db.get_location_at_time(2021, 1, 15, 15, 45)
        assert location["latitude"] == 37.7749
        assert location["longitude"] == -122.4194

        # Test outside intervals (should return None)
        location = db.get_location_at_time(2020, 1, 1, 12, 0)
        assert location["latitude"] is None
        assert location["longitude"] is None

    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache")
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)


def test_cache_validation():
    """Test that cache is invalidated when source file changes."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        create_test_timeline_file(f.name)
        temp_file = f.name

    try:
        # Create initial database and cache
        db1 = MyTimelineDB(temp_file)
        original_hash = db1._source_hash

        # Modify the file
        with open(temp_file, 'r') as f:
            data = json.load(f)
        data.append({
            "visit": {
                "topCandidate": {
                    "placeLocation": {
                        "latitude": 40.7128,
                        "longitude": -74.0060
                    }
                }
            },
            "startTime": "2021-01-16T10:00:00Z",
            "endTime": "2021-01-16T11:00:00Z"
        })
        with open(temp_file, 'w') as f:
            json.dump(data, f)

        # Create new instance - should detect change and rebuild
        db2 = MyTimelineDB(temp_file)
        assert db2._source_hash != original_hash
        assert len(db2._time_idx) == 4  # Should have 4 intervals now

    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache")
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)


def test_cache_roundtrip():
    """Test cache save and load functionality."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        create_test_timeline_file(f.name)
        temp_file = f.name

    try:
        # Create database and save cache
        db1 = MyTimelineDB(temp_file)
        n1 = len(db1._time_idx)

        # Save to test cache directory
        test_cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache_test")
        current_hash = db1._get_file_hash(temp_file)
        db1._save_cache(test_cache_dir, current_hash)

        # Load from test cache
        db2 = MyTimelineDB(temp_file)
        success = db2._load_cache(test_cache_dir, current_hash)
        assert success
        n2 = len(db2._time_idx)

        assert n1 == n2
        assert n1 > 0

    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache")
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)
        test_cache_dir = os.path.join(os.path.dirname(temp_file), ".timeline_cache_test")
        if os.path.exists(test_cache_dir):
            import shutil
            shutil.rmtree(test_cache_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])