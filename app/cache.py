"""
Minimal in-memory query cache.

Every successful upload bumps the data version, which effectively
invalidates all previously cached query results without needing to
track individual keys. This is what keeps repeat dashboard requests
(same filters, same data) fast on large datasets.
"""
_cache: dict = {}
_data_version = 0


def bump_version() -> None:
    global _data_version
    _data_version += 1
    _cache.clear()


def cache_get(key):
    return _cache.get((_data_version, key))


def cache_set(key, value) -> None:
    _cache[(_data_version, key)] = value
