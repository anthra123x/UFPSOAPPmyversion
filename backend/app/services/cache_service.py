import time
from typing import Any, Dict, Optional, Tuple

class MemoryCache:
    """
    Caché en memoria de ultra-alta velocidad (sub-milisegundo).
    Reduce las consultas repetitivas a Neon PostgreSQL sobre TLS.
    """
    def __init__(self):
        # key -> (value, expire_timestamp)
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        val, expire_at = self._store[key]
        if expire_at is not None and time.time() > expire_at:
            del self._store[key]
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Almacena un valor con TTL (por defecto 5 minutos)."""
        expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else None
        self._store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def delete_prefix(self, prefix: str) -> int:
        """Invalida todas las claves que comiencen con el prefijo dado."""
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]
        return len(keys_to_delete)

    def clear(self) -> None:
        self._store.clear()

# Singleton global de caché en memoria
cache = MemoryCache()
