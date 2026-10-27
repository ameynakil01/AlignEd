import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

MAX_HEARTBEAT_CHUNK_SECONDS = 30.0  # Max single interval allowable per heartbeat to prevent instant spoofing
VERIFICATION_THRESHOLD_PERCENT = 75.0  # Threshold required to unlock micro-quiz


def merge_watch_intervals(
    existing_intervals: List[List[float]],
    new_interval: List[float],
    total_duration: float
) -> Tuple[List[List[float]], float, float, bool, bool]:
    """
    Merges a new watch interval into existing intervals using an anti-cheat aggregation algorithm.
    
    Prevents scrub-skipping:
    - Rejects invalid intervals (e.g. end <= start, negative timestamps).
    - Clamps intervals to [0, total_duration].
    - Caps individual interval chunks to MAX_HEARTBEAT_CHUNK_SECONDS to stop spoofed large intervals.
    - Merges overlapping or adjacent contiguous intervals.
    - Calculates unique non-overlapping watch time.
    
    Returns:
        (merged_intervals, unique_seconds, watch_percentage, video_verified, quiz_unlocked)
    """
    if total_duration <= 0:
        total_duration = 300.0  # Safe default if duration not yet resolved by player

    valid_intervals: List[Tuple[float, float]] = []

    # Clean existing intervals
    for item in existing_intervals or []:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            s, e = float(item[0]), float(item[1])
            if e > s and s >= 0:
                s = max(0.0, s)
                e = min(total_duration, e)
                if e > s:
                    valid_intervals.append((s, e))

    # Process new interval
    if isinstance(new_interval, (list, tuple)) and len(new_interval) == 2:
        new_start = float(new_interval[0])
        new_end = float(new_interval[1])

        # Basic validity checks
        if new_end > new_start and new_start >= 0 and new_start < total_duration:
            new_start = max(0.0, new_start)
            new_end = min(total_duration, new_end)

            # Anti-spoofing cap: single heartbeat interval cannot exceed chunk cap
            chunk_duration = new_end - new_start
            if chunk_duration > MAX_HEARTBEAT_CHUNK_SECONDS:
                logger.warning(
                    f"Heartbeat interval duration {chunk_duration}s exceeded cap of {MAX_HEARTBEAT_CHUNK_SECONDS}s. Clamping."
                )
                new_end = new_start + MAX_HEARTBEAT_CHUNK_SECONDS

            if new_end > new_start:
                valid_intervals.append((new_start, new_end))

    if not valid_intervals:
        return [], 0.0, 0.0, False, False

    # Sort intervals by start time
    sorted_intervals = sorted(valid_intervals, key=lambda x: x[0])

    # Merge overlapping or contiguous intervals (tolerating up to 1.5s delta gap)
    merged: List[List[float]] = []
    current_start, current_end = sorted_intervals[0]

    for next_start, next_end in sorted_intervals[1:]:
        if next_start <= current_end + 1.5:  # Overlapping or contiguous
            current_end = max(current_end, next_end)
        else:
            merged.append([round(current_start, 2), round(current_end, 2)])
            current_start, current_end = next_start, next_end

    merged.append([round(current_start, 2), round(current_end, 2)])

    # Compute genuine unique seconds
    unique_seconds = sum(interval[1] - interval[0] for interval in merged)
    unique_seconds = round(min(total_duration, unique_seconds), 2)

    # Compute percentage
    watch_percentage = round(min(100.0, (unique_seconds / total_duration) * 100.0), 1)

    video_verified = watch_percentage >= VERIFICATION_THRESHOLD_PERCENT
    quiz_unlocked = video_verified

    return merged, unique_seconds, watch_percentage, video_verified, quiz_unlocked

