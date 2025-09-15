"""
Tests for the timeline database functionality.

These tests verify the core timeline parsing and query capabilities.
"""

import pytest
import tempfile
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch

from where_was_eye.timeline_db import MyTimelineDB, extract_interval, parse_dt_loose


class TestTimelineDatabase:
    """Test suite for timeline database functionality."""
    
    def test_parse_dt_loose_valid_formats(self):
        """Test parsing various datetime formats."""
        test_cases = [
            ("2024-08-20T15:30:00Z", datetime(2024, 8, 20, 15, 30)),
            ("2024-08-20T15:30:00+00:00", datetime(2024, 8, 20, 15, 30)),
            ("2024-08-20T15:30:00", datetime(2024, 8, 20, 15, 30)),
        ]
        
        for input_str, expected_dt in test_cases:
            result = parse_dt_loose(input_str)
            assert result == expected_dt, f"Failed to parse: {input_str}"
    
    def test_parse_dt_loose_invalid(self):
        """Test parsing invalid datetime strings."""
        invalid_cases = [
            "invalid-date",
            "2024-13-45T99:99:99",  # Invalid components
            "",
            None,
            12345,  # Not a string
        ]
        
        for invalid_input in invalid_cases:
            result = parse_dt_loose(invalid_input)
            assert result is None, f"Should return None for: {invalid_input}"
    
    def test_extract_interval_from_json(self):
        """Test extracting intervals from JSON strings."""
        test_json = '''
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
        }
        '''
        
        start_dt, end_dt, meta = extract_interval(test_json)
        assert start_dt == datetime(2024, 8, 20, 15, 30)
        assert end_dt == datetime(2024, 8, 20, 16, 30)
        assert meta["start_raw"] == "2024-08-20T15:30:00Z"
        assert meta["end_raw"] == "2024-08-20T16:30:00Z"
    
    def test_extract_interval_missing_times(self):
        """Test extracting intervals when times are missing."""
        test_json = '{"someOtherField": "value"}'
        start_dt, end_dt, meta = extract_interval(test_json)
        assert start_dt is None
        assert end_dt is None
    
    def test_database_initialization(self):
        """Test database initialization with mock data."""
        # Create a temporary timeline JSON file
        mock_timeline_data = [
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_timeline_data, f)
            temp_file = f.name
        
        try:
            # Test database initialization
            db = MyTimelineDB(temp_file)
            
            # Should have created time index and data
            assert db._time_idx is not None
            assert db._all_data is not None
            assert len(db._time_idx) == 2
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file)
    
    @patch('where_was_eye.timeline_db.pd.IntervalIndex')
    @patch('where_was_eye.timeline_db.pd.Timestamp')
    def test_get_location_at_time_found(self, mock_timestamp, mock_interval_index):
        """Test getting location when time is found in interval."""
        # Mock the interval index and data
        mock_interval = Mock()
        mock_interval.contains.return_value = [True, False]  # First interval contains the time
        mock_interval_index.from_tuples.return_value = mock_interval
        
        mock_timestamp.return_value = Mock()
        
        # Mock timeline data with a visit entry
        mock_data = [
            {
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
                "activity": {
                    "start": {
                        "latitude": 40.7580, 
                        "longitude": -73.9855
                    }
                }
            }
        ]
        
        db = MyTimelineDB("dummy_path")
        db._time_idx = mock_interval
        db._all_data = mock_data
        
        # Mock the find_interval_or_nearest function
        with patch('where_was_eye.timeline_db.find_interval_or_nearest') as mock_find:
            mock_find.return_value = (0, True)  # First interval, contains time
            
            location = db.get_location_at_time(2024, 8, 20, 15, 30)
            
            assert location["latitude"] == 40.7128
            assert location["longitude"] == -74.0060
    
    @patch('where_was_eye.timeline_db.find_interval_or_nearest')
    def test_get_location_at_time_not_found(self, mock_find):
        """Test getting location when time is not found."""
        mock_find.return_value = (0, False)  # First interval, but doesn't contain time
        
        db = MyTimelineDB("dummy_path")
        db._time_idx = Mock()
        db._all_data = [{}]  # Empty data
        
        location = db.get_location_at_time(2024, 8, 20, 15, 30)
        
        assert location["latitude"] is None
        assert location["longitude"] is None
    
    def test_get_location_activity_type(self):
        """Test getting location from activity entries."""
        db = MyTimelineDB("dummy_path")
        db._time_idx = Mock()
        
        # Mock data with activity entry
        mock_data = [
            {
                "activity": {
                    "start": {
                        "latitude": 40.7580,
                        "longitude": -73.9855
                    }
                }
            }
        ]
        db._all_data = mock_data
        
        # Mock finding the interval
        with patch('where_was_eye.timeline_db.find_interval_or_nearest') as mock_find:
            mock_find.return_value = (0, True)
            
            location = db.get_location_at_time(2024, 8, 20, 15, 30)
            
            assert location["latitude"] == 40.7580
            assert location["longitude"] == -73.9855


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_database_file_not_found(self):
        """Test behavior when database file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            MyTimelineDB("/non/existent/path.json")
    
    def test_invalid_json_file(self):
        """Test behavior with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                MyTimelineDB(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_empty_database_file(self):
        """Test behavior with empty JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            temp_file = f.name
        
        try:
            db = MyTimelineDB(temp_file)
            # Should initialize without errors but with empty data
            assert db._time_idx is not None
            assert db._all_data == []
        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])