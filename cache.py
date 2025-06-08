import time
from typing import Any, Callable

cache_store = {}

def _get_cache(key: str, expire: int):
    data = cache_store.get(key)
    if not data:
        return None
    value, ts = data
    if time.time() - ts > expire:
        del cache_store[key]
        return None
    return value

def _set_cache(key: str, value: Any):
    cache_store[key] = (value, time.time())

def use_cache(key: str, expire: int, func: Callable, *args, **kwargs):
    cached = _get_cache(key, expire)
    if cached is not None:
        return cached

    result = func(*args, **kwargs)
    _set_cache(key, result)
    return result
