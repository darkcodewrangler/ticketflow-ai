def get_value(obj, key, default=None):
    """
    Handle both object attributes and dictionary keys
    """
    if hasattr(obj, key):
        return getattr(obj, key, default)
    elif isinstance(obj, dict): 
        return obj.get(key, default)
    return default