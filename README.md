# Redis cache for Python

- Simple python redis cache library, mostly used as [distributed caching](https://redis.com/glossary/distributed-caching), where application servers is in separated processes such as Gunicorn workers, K8s replicas, .etc..
- **Asyncio Support for FastAPI, Starlette**

## Requirements

- Redis 5+
- Python 3.6+

## Installation

```bash
$ pip install py-redis-cache
```

## Simple usage

```python
from py_redis_cache import RedisCache

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
```

**Asynchronous with asyncio**

```python
import asyncio
from py_redis_cache.asyncio import AsyncRedisCache

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

# Cache added, key=redis_cache::11=__main__.heavy_compute(a=[1, 2, 3].b=[4, 5, 6]), size=0.000Kb
# [4, 10, 18]
# Cache hit, key=redis_cache::11=__main__.heavy_compute(a=[1, 2, 3].b=[4, 5, 6])
# [4, 10, 18]
```

## Advanced usage

for further examples and use cases please visit [examples](examples)

## Testing

**NOTE**: Please make sure you have redis running on `127.0.0.1:6379` to run test.

```bash
$ python3 -m unittest discover tests
```
