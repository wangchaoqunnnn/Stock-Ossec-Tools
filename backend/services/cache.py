# -*- coding: utf-8 -*-
"""轻量 TTL 内存缓存（线程安全）。"""

import threading
import time


class TTLCache(object):
    """带过期时间的简单内存缓存。

    用法::

        cache = TTLCache(ttl=10)
        cache.set("key", value)
        value = cache.get("key")
    """

    def __init__(self, ttl=10):
        self._ttl = ttl
        self._lock = threading.Lock()
        self._data = {}

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < time.time():
                self._data.pop(key, None)
                return None
            return value

    def set(self, key, value):
        with self._lock:
            self._data[key] = (time.time() + self._ttl, value)

    def clear(self):
        with self._lock:
            self._data.clear()
