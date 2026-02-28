"""
IST Timezone Utility
ALL datetime operations must use IST (Indian Standard Time)
"""
from datetime import datetime
import pytz

# IST timezone object
IST = pytz.timezone('Asia/Kolkata')

def now_ist():
    """Get current time in IST"""
    return datetime.now(IST)

def utc_to_ist(dt):
    """Convert UTC datetime to IST"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = pytz.utc.localize(dt)
    return dt.astimezone(IST)

def ist_to_utc(dt):
    """Convert IST datetime to UTC (for storage)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume IST if no timezone
        dt = IST.localize(dt)
    return dt.astimezone(pytz.utc)

def parse_datetime_ist(dt_string):
    """Parse datetime string and ensure it's in IST"""
    if not dt_string:
        return None
    
    try:
        # Remove 'Z' and replace with +00:00
        dt_string = dt_string.replace('Z', '+00:00')
        
        # Parse the datetime
        if '+' in dt_string or dt_string.endswith('00:00'):
            # Has timezone info
            dt = datetime.fromisoformat(dt_string)
        else:
            # No timezone - treat as IST
            dt = datetime.fromisoformat(dt_string)
            dt = IST.localize(dt)
        
        return dt
    except Exception as e:
        print(f"Error parsing datetime: {dt_string}, error: {e}")
        return None

def format_ist(dt, format_str='%Y-%m-%d %I:%M %p'):
    """Format datetime in IST"""
    if dt is None:
        return ''
    
    # Ensure it's in IST
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    else:
        dt = dt.astimezone(IST)
    
    return dt.strftime(format_str)
