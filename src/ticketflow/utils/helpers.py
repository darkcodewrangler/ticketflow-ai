import datetime


def get_value(obj, key, default=None):
    """
    Handle both object attributes and dictionary keys
    """
    if hasattr(obj, key):
        return getattr(obj, key, default)
    elif isinstance(obj, dict): 
        return obj.get(key, default)
    return default

def utcnow() -> datetime.datetime:
    """
    Get current UTC time as datetime
    """
    return datetime.datetime.now(datetime.UTC)

def get_isoformat(dt: datetime.datetime = utcnow()) -> str:

    """
    Get datetime as string
    """
    return dt.isoformat()
