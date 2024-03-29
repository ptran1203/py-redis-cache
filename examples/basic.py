import sys
sys.path.append(".")

from py_redis_cache import RedisCache
from py_redis_cache.functional import cache

# init redis_cache instance and connection
redis_cache = RedisCache(
    host="127.0.0.1",
    port=6379,
    verbose=1  # Turn on logging for demonstration, set to 0 for silent caching
)

@redis_cache.cache(ttl=10)  # Expire after 10 seconds
def heavy_compute(a: list, b: list):
    length = max(len(a), len(b))
    c = [[]] * length
    for i in range(length):
        c[i] = a[i] * b[i]
    return c

result =  heavy_compute([1, 2, 3], [4, 5, 6])
print(result)
# Cache added, key=redis_cache::11=__main__.heavy_compute(a=[1, 2, 3].b=[4, 5, 6]), size=0.000Kb
# [4, 10, 18]

result =  heavy_compute([1, 2, 3], [4, 5, 6])
print(result)
# Cache hit, key=redis_cache::11=__main__.heavy_compute(a=[1, 2, 3].b=[4, 5, 6])
# [4, 10, 18]