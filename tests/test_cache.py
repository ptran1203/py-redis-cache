import os
import time
import unittest
from redis_cache_py import RedisCache, Singleton


class TestRedisCache(unittest.TestCase):

    def test_simple_cache(self):
        # Enable Singleton for testing this case
        redis_cache = RedisCache()
        redis_cache2 = RedisCache()

        assert redis_cache is redis_cache2  # Sample object

    def test_ttl(self):
        redis_cache = RedisCache()

        @redis_cache.cache(ttl=1)
        def add_two(a, b):
            return a + b + time.time()

        result = add_two(1, 2)
        result_2 = add_two(1, 2)

        assert result == result_2  # Should cached

        time.sleep(1.1) # Cache will expire after 1 seconds

        assert result != add_two(1, 2)

    def test_kwargs(self):
        redis_cache = RedisCache()

        @redis_cache.cache(ttl=1)
        def add_two(a, b):
            return a + b + time.time()
        
        result = add_two(1, 2)
        result_2 = add_two(1, b=2)
        result_3 = add_two(a=1, b=2)  
        assert result == result_2 == result_3


if __name__ == '__main__':
    unittest.main()
