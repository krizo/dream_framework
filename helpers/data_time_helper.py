"""Time formatting helper functions."""
from datetime import datetime
from typing import Optional


def format_duration(duration_seconds: float) -> str:
    """
    Format duration into human-readable string with appropriate units.
    Shows only non-zero values.

    @param duration_seconds: Duration in seconds
    @return: Formatted string with appropriate unit (ms, s, m)
    Examples:
        0.123 -> "123ms"
        1.5 -> "1.5s"
        65.0 -> "1m 5s"
    """
    if duration_seconds is None:
        return "N/A"

    if duration_seconds == 0:
        return "0ms"

    if duration_seconds < 0.001:  # Less than 1ms
        return "<1ms"

    if duration_seconds < 1:  # Less than 1 second
        return f"{int(duration_seconds * 1000)}ms"

    if duration_seconds < 60:  # Less than 1 minute
        return f"{duration_seconds:.2f}s"

    # More than 1 minute
    minutes = int(duration_seconds // 60)
    seconds = duration_seconds % 60
    if seconds < 0.1:  # If seconds are negligible
        return f"{minutes}m"
    return f"{minutes}m {seconds:.1f}s"


def format_timestamp(timestamp: Optional[datetime]) -> str:
    """
    Format timestamp without microseconds.

    @param timestamp: Datetime object to format
    @return: Formatted timestamp string or 'N/A' if None
    """
    if timestamp is None:
        return "N/A"

    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def calculate_duration(start: Optional[datetime], end: Optional[datetime]) -> Optional[float]:
    """
    Calculate duration between two timestamps.

    @param start: Start timestamp
    @param end: End timestamp
    @return: Duration in seconds or None if timestamps are invalid
    """
    if not start or not end:
        return None

    return (end - start).total_seconds()