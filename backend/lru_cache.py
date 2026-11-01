import time
import threading
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity=32, ttl_seconds=60):
        self.capacity = capacity
        self.ttl = ttl_seconds
        self._data = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                self.misses += 1
                return None
            value, saved_at = item
            if time.time() - saved_at > self.ttl:
                del self._data[key]
                self.misses += 1
                return None
            self._data.move_to_end(key)
            self.hits += 1
            return value

    def put(self, key, value):
        with self._lock:
            self._data[key] = (value, time.time())
            self._data.move_to_end(key)
            if len(self._data) > self.capacity:
                self._data.popitem(last=False)

    def invalidate(self, key):
        with self._lock:
            self._data.pop(key, None)

    def stats(self):
        with self._lock:
            return {"size": len(self._data), "capacity": self.capacity,
                    "hits": self.hits, "misses": self.misses}