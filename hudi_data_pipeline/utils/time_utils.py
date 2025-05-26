from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

def get_batch_time_window(minutes: int = 5) -> Tuple[datetime, datetime]:
    """
    Get the start and end time for the current batch window
    
    Args:
        minutes: Size of the time window in minutes
        
    Returns:
        Tuple of (start_time, end_time) as datetime objects
    """
    current_time = datetime.now()
    start_time = current_time - timedelta(minutes=minutes)
    return start_time, current_time

def format_hudi_timestamp(dt: datetime) -> str:
    """
    Format a datetime object for Hudi incremental queries
    
    Args:
        dt: Datetime to format
        
    Returns:
        String formatted for Hudi
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")

def get_batch_metadata(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """
    Create standard batch metadata dictionary
    
    Args:
        start_time: Batch start time
        end_time: Batch end time
        
    Returns:
        Dictionary with batch metadata
    """
    batch_id = end_time.strftime("%Y%m%d%H%M%S")
    
    return {
        "batch_id": batch_id,
        "start_time": format_hudi_timestamp(start_time),
        "end_time": format_hudi_timestamp(end_time),
        "batch_date": end_time.strftime("%Y-%m-%d"),
        "batch_hour": end_time.strftime("%H"),
        "batch_minute": end_time.strftime("%M")
    }
