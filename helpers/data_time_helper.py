def format_duration(duration_seconds: float) -> str:
    """
    Format duration into human-readable string with appropriate units.
    Shows only non-zero values.

    @param duration_seconds: float - Duration in seconds
    @return str - Formatted duration string like "1h 10m 5s 100ms"
    """
    # Convert to milliseconds for precision
    total_ms = int(duration_seconds * 1000)

    hours, remainder = divmod(total_ms, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)

    parts = []

    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        parts.append(f"{seconds}s")
    if milliseconds > 0:
        parts.append(f"{milliseconds}ms")

    # If duration is 0, return "0ms"
    if not parts:
        return "0ms"

    return " ".join(parts)