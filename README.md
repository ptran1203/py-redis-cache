# Redis cache for Python

- Simple python redis cache library, mostly used as distributed caching, where application servers is in separated processes such as Gunicorn workers, K8s replicas.
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

for further examples and use cases please visit [examples](examples)
