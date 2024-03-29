import os
import unittest
from redis_cache_py import RedisCache, Singleton


class TestRedisCacheConnection(unittest.TestCase):

    def test_two_calls(self):
        # Enable Singleton for testing this case
        Singleton.disable = False

        redis_cache = RedisCache()
        redis_cache2 = RedisCache()

        assert redis_cache is redis_cache2  # Sample object

    def test_current_redis_cache(self):
        # Enable Singleton for testing this case
        Singleton.disable = False

        redis_cache = RedisCache()
        
        from redis_cache_py import current_redis_cache

        assert redis_cache is current_redis_cache  # Sample object


if __name__ == '__main__':
    unittest.main()