

def cache(tags=None, ttl=30):
    from . import current_redis_cache
    return current_redis_cache.cache(tags, ttl)


def aio_cache(tags=None, ttl=30):
    from . import current_aio_redis_cache
    return current_aio_redis_cache.cache(tags, ttl)
