"""Business date of UTC audit timestamps, without rewriting historical events."""
from datetime import datetime

def event_day(value,zone=None):
    if not value:return None
    if len(value)==10:return value
    stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    return stamp.astimezone(zone).date().isoformat()
