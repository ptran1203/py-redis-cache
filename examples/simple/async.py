# Example of caching async functions

import sys
sys.path.append(".")
import asyncio
from redis_cache_py.asyncio import AsyncRedisCache

# init redis_cache instance and connection
redis_cache = AsyncRedisCache(
    host="127.0.0.1",
    port=6379,
    verbose=1  # Turn on logging for demonstration, set to 0 for silent caching
)

@redis_cache.aio_cache(ttl=10)  # Expire after 10 seconds
async def heavy_compute(a: list, b: list):
    length = max(len(a), len(b))
    c = [[]] * length
    for i in range(length):
        c[i] = a[i] * b[i]
    return c

async def test_async_cache():
    result = await heavy_compute([1, 2, 3], [4, 5, 6])
    print(result)

    # Now the result is cached
    result2 = await heavy_compute([1, 2, 3], [4, 5, 6])

    print(result2)

loop = asyncio.get_event_loop()
loop.run_until_complete(test_async_cache())