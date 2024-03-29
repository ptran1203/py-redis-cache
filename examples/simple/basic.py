import sys
sys.path.append(".")

from py_redis_cache import RedisCache

# init redis_cache instance and connection
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
