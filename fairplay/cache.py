import time

from flask import current_app
from flask_caching import Cache as _Cache


class Cache(_Cache):
    def stale_if_error(self, f=None, cache_key=None, max_stale=None, ttl=None):
        """Return stale cached result if an error occurs."""

        def decorator(f):
            def wrapper(*args, **kwargs):
                cache_defaults = current_app.config.get_namespace(
                    "CACHE_DEFAULT_"
                )

                nonlocal ttl
                if not ttl:
                    ttl = cache_defaults["timeout"]

                cached_value = self.get(cache_key)
                if cached_value and cached_value["iat"] + ttl < time.time():
                    return cached_value["value"]

                try:
                    value = f(*args, **kwargs)
                except Exception:
                    if cached_value:
                        current_app.logger.warning(
                            "Error calling '%s', returning stale result",
                            f,
                            exc_info=True,
                        )
                        return cached_value["value"]
                    raise

                nonlocal max_stale
                if not max_stale:
                    max_stale = cache_defaults["stale_timeout"]

                self.set(
                    cache_key, {"iat": time.time(), "value": value}, max_stale
                )

                return value

            return wrapper

        return f and decorator(f) or decorator


cache = shared_cache = Cache()
worker_cache = Cache()


def init_cache(app):
    if app.config.get("CACHE_TYPE") == "RedisCache":
        app.config.setdefault("CACHE_REDIS_URL", app.config.get("REDIS_URL"))

    shared_cache.init_app(app)

    worker_config = app.config.get_namespace("CACHE_WORKER_")
    worker_config.setdefault("cache_type", "SimpleCache")

    worker_cache.init_app(app, worker_config)
