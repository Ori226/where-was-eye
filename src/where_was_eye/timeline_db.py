"""
Google Timeline Database Parser

This module provides functionality to parse and query Google Timeline location history data.
It handles the JSON format from Google Takeout and provides efficient time-based queries.
"""

import json
import os
import pickle
import re
import ast
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List, Any
import numpy as np
import pandas as pd
from tqdm import tqdm

# Optional dependencies for enhanced parsing
try:
    import json5
except ImportError:
    json5 = None

try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None

logger = logging.getLogger(__name__)

# Regex patterns for parsing timeline data
ISO_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T"
    r"\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,6})?"
    r"(?:Z|[+-]\d{2}:\d{2})"
)

KEYVAL_RE = re.compile(
    r"""(?:
            ["'](?P<key>startTime|endTime|start_time|end_time|start|end)["']\s*:\s*
            ["'](?P<val>[^"']+)["']
        )""",
    re.IGNORECASE | re.VERBOSE
)


def parse_loose_mapping(text: str) -> Optional[Dict]:
    """Parse JSON-like text with various formatting options."""
    # Try strict JSON
    try:
        return json.loads(text)
    except Exception:
        pass
    
    # Try JSON5 if available
    if json5:
        try:
            return json5.loads(text)
        except Exception:
            pass
    
    # Try Python literal (handles single quotes)
    try:
        return ast.literal_eval(text)
    except Exception:
        pass
    
    return None


def parse_dt_loose(s: str) -> Optional[datetime]:
    """Parse datetime strings with various formats."""
    if not isinstance(s, str):
        return None
    
    t = s.strip()
    # Handle 'Z' -> '+00:00' for fromisoformat compatibility
    if t.endswith('Z'):
        t = t[:-1] + '+00:00'
    
    try:
        return datetime.fromisoformat(t)
    except Exception:
        pass
    
    if dateutil_parser:
        try:
            return dateutil_parser.isoparse(s)
        except Exception:
            pass
    
    return None


def extract_interval(text: str) -> Tuple[Optional[datetime], Optional[datetime], Dict]:
    """
    Extract start and end datetime from timeline entry text.
    
    Returns:
        Tuple of (start_dt, end_dt, meta) where meta includes raw strings found.
    """
    start_raw = end_raw = None

    # 1) Try to parse as mapping
    obj = parse_loose_mapping(text)
    if isinstance(obj, dict):
        # Common key variants
        for k in ['startTime', 'start_time', 'start']:
            if k in obj and isinstance(obj[k], str):
                start_raw = obj[k]
                break
        for k in ['endTime', 'end_time', 'end']:
            if k in obj and isinstance(obj[k], str):
                end_raw = obj[k]
                break

    # 2) If not found, try key/value regex
    if start_raw is None or end_raw is None:
        found = {}
        for m in KEYVAL_RE.finditer(text):
            key = m.group('key').lower()
            val = m.group('val')
            found[key] = val
        start_raw = start_raw or found.get('starttime') or found.get('start_time') or found.get('start')
        end_raw = end_raw or found.get('endtime') or found.get('end_time') or found.get('end')

    # 3) If still missing, pull first two ISO timestamps in order
    if start_raw is None or end_raw is None:
        hits = ISO_RE.findall(text)
        if hits:
            if start_raw is None and len(hits) >= 1:
                start_raw = hits[0]
            if end_raw is None and len(hits) >= 2:
                end_raw = hits[1]

    start_dt = parse_dt_loose(start_raw) if start_raw else None
    end_dt = parse_dt_loose(end_raw) if end_raw else None

    meta = {'start_raw': start_raw, 'end_raw': end_raw}
    return start_dt, end_dt, meta


def to_utc_naive(x, assume_utc_for_naive=True) -> pd.Timestamp:
    """Convert timestamp to UTC-naive format."""
    ts = pd.Timestamp(x)
    if ts.tz is None:
        # Option A: treat naive as UTC for consistency
        return ts.tz_localize('UTC').tz_localize(None) if assume_utc_for_naive else ts
    # Convert tz-aware to UTC, then drop tz
    return ts.tz_convert('UTC').tz_localize(None)


def find_interval_or_nearest(time_idx: pd.IntervalIndex, t) -> Tuple[int, bool]:
    """
    Find the interval containing a timestamp or the nearest interval.
    
    Returns:
        Tuple of (position, contains) where contains indicates if timestamp is within interval.
    """
    t = pd.Timestamp(t)
    if t.tz is not None:
        t = t.tz_convert('UTC').tz_localize(None)

    mask = time_idx.contains(t)
    mask_np = np.asarray(mask, dtype=bool)
    if mask_np.any():
        pos = int(np.flatnonzero(mask_np)[0])
        return pos, True

    # Distances via int64 ns to avoid .abs() on TimedeltaIndex
    left_delta = (t - time_idx.left)            # TimedeltaIndex
    right_delta = (time_idx.right - t)          # TimedeltaIndex
    left_ns = np.abs(left_delta.asi8)           # int64 nanoseconds
    right_ns = np.abs(right_delta.asi8)         # int64 nanoseconds
    dist_ns = np.minimum(left_ns, right_ns)
    pos = int(dist_ns.argmin())
    return pos, False


class MyTimelineDB:
    """Main class for parsing and querying Google Timeline location history."""
    
    def __init__(self, db_path: str):
        """
        Initialize the timeline database.
        
        Args:
            db_path: Path to the Google Timeline JSON file
        """
        self.db_path = db_path
        self._time_idx = None
        self._all_data = None
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize the database, loading from cache if available."""
        cache_dir = os.path.join(os.path.dirname(self.db_path), ".timeline_cache")
        if self._load_cache(cache_dir):
            logger.info("Loaded timeline data from cache at %s", cache_dir)
            return

        logger.info("Loading timeline data from %s", self.db_path)
        with open(self.db_path, 'r') as fp:
            all_history = json.load(fp)
        logger.info("Done loading timeline data from %s", self.db_path)
        
        all_interval_tuples = []
        for item in tqdm(all_history, desc="Processing timeline entries"):
            if 'visit' not in item and 'activity' not in item and "timelinePath" not in item:
                continue  # skip non-interval entries
            
            start_dt, end_dt, _ = extract_interval(json.dumps(item))
            if start_dt is None or end_dt is None:
                continue
            
            s = to_utc_naive(start_dt)
            e = to_utc_naive(end_dt)
            if s > e:  # optional guard
                s, e = e, s
            all_interval_tuples.append((s, e))

        self._time_idx = pd.IntervalIndex.from_tuples(all_interval_tuples, closed='both')
        self._all_data = all_history
        
        # Save cache for fast reloads
        try:
            self._save_cache(cache_dir)
            logger.info("Saved timeline cache to %s", cache_dir)
        except Exception as e:
            logger.warning("Failed to save timeline cache: %s", e)

    def _save_cache(self, cache_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Persist parsed data for fast reloads.
        
        Returns:
            Dict with written file paths
        """
        if self._time_idx is None or self._all_data is None:
            raise ValueError("Nothing to cache yet: _time_idx/_all_data are None")

        cache_dir = cache_dir or os.path.join(os.path.dirname(self.db_path), ".timeline_cache")
        os.makedirs(cache_dir, exist_ok=True)

        # Store IntervalIndex efficiently as int64 nanoseconds
        left_ns = self._time_idx.left.asi8
        right_ns = self._time_idx.right.asi8
        intervals_path = os.path.join(cache_dir, "intervals.npz")
        np.savez(intervals_path, left_ns=left_ns, right_ns=right_ns)

        # Store all_data via pickle for fastest Python loads
        all_data_path = os.path.join(cache_dir, "all_data.pkl")
        with open(all_data_path, "wb") as f:
            pickle.dump(self._all_data, f, protocol=pickle.HIGHEST_PROTOCOL)

        return {"intervals": intervals_path, "all_data": all_data_path}

    def _load_cache(self, cache_dir: Optional[str] = None) -> bool:
        """
        Load previously cached timeline data.
        
        Returns:
            True if successful
        """
        cache_dir = cache_dir or os.path.join(os.path.dirname(self.db_path), ".timeline_cache")
        intervals_path = os.path.join(cache_dir, "intervals.npz")
        all_data_path = os.path.join(cache_dir, "all_data.pkl")

        if not (os.path.exists(intervals_path) and os.path.exists(all_data_path)):
            return False

        try:
            arrs = np.load(intervals_path)
            left = pd.to_datetime(arrs["left_ns"])  # from int64 ns
            right = pd.to_datetime(arrs["right_ns"])  # from int64 ns
            self._time_idx = pd.IntervalIndex.from_arrays(left, right, closed='both')
            with open(all_data_path, "rb") as f:
                self._all_data = pickle.load(f)
            return True
        except Exception as e:
            logger.warning("Failed loading timeline cache from %s: %s", cache_dir, e)
            return False
        
    def get_location_at_time(self, year: int, month: int, day: int, hour: int, minute: int) -> Dict[str, float]:
        """
        Get location at a specific time.
        
        Args:
            year, month, day, hour, minute: Time components
            
        Returns:
            Dict with latitude and longitude, or None values if not found
        """
        if self._time_idx is None or self._all_data is None:
            return {"latitude": None, "longitude": None}
            
        t = pd.Timestamp(year=year, month=month, day=day, hour=hour, minute=minute, second=0)
        pos, contains = find_interval_or_nearest(self._time_idx, t)
        
        if not contains:
            return {"latitude": None, "longitude": None}
            
        item = self._all_data[pos]
        
        if 'visit' in item:
            return item['visit']['topCandidate']['placeLocation']
        elif 'activity' in item:
            # TODO: better handling of activities by relating to start/end times
            return item['activity']['start']
        
        return {"latitude": None, "longitude": None}


def main():
    """Example usage of the timeline database."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    
    # Example usage - this would need to be configured with actual path
    db = MyTimelineDB('/path/to/your/location-history.json')
    location = db.get_location_at_time(2021, 1, 15, 15, 30)
    print(f"Location: {location}")


if __name__ == "__main__":
    main()