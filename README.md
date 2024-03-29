![example branch parameter](https://github.com/ptran1203/py-redis-cache/actions/workflows/run-unittest.yml/badge.svg)

# Redis cache for Python

- Simple python redis cache library, mostly used for [distributed caching](https://redis.com/glossary/distributed-caching), where applications is running on separated processes such as Gunicorn workers, K8s replicas, Cloud, ...
- **Asyncio Support for FastAPI, Starlette**

## Requirements

- Redis 5+
- Python 3.6+

## Installation

```bash
$ pip install redis-cache-py
```

## Simple usage

```python
from redis_cache_py import RedisCache

# init redis_cache instance and connection
# make sure you have redis running on `127.0.0.1:6379`
redis_cache = RedisCache(
    host="127.0.0.1",
    port=6379,
)

@redis_cache.cache(ttl=10)  # Expire after 10 seconds
def concate_list(a: list, b: list):
    print("This function is called")
    return a + b

result =  concate_list([1, 2, 3], [4, 5, 6])
print(result)
# This function is called
# [1, 2, 3, 4, 5, 6]

# Now result is cached, next time you call this function, result will returned
# from redis
result =  concate_list([1, 2, 3], [4, 5, 6])
print(result)
# [1, 2, 3, 4, 5, 6]
```

**Asynchronous with asyncio**

```python
import asyncio
from redis_cache_py.asyncio import AsyncRedisCache

# init redis_cache instance and connection
# Make sure you have redis running on `127.0.0.1:6379`
redis_cache = AsyncRedisCache(
    host="127.0.0.1",
    port=6379,
    verbose=1  # Turn on logging for demonstration, set to 0 for silent caching
)

@redis_cache.aio_cache(ttl=10)  # Expire after 10 seconds
async def concate_list(a: list, b: list):
    print("This function is called")
    return a + b

async def test_async_cache():
    result = await concate_list([1, 2, 3], [4, 5, 6])
    print(result)

    # Now the result is cached
    result2 = await concate_list([1, 2, 3], [4, 5, 6])

    print(result2)

loop = asyncio.get_event_loop()
loop.run_until_complete(test_async_cache())

# Output:
# This function is called
# [1, 2, 3, 4, 5, 6]
# [1, 2, 3, 4, 5, 6]
```

## Advanced usage

for further examples and use cases please visit [examples](examples)

## Testing

**NOTE**: Please make sure you have redis running on `127.0.0.1:6379` to run test.

```bash
$ python3 -m unittest discover tests
```
