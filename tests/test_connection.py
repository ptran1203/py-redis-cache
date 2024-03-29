# Test redis cache connection from environment variable or argument passing to
# RedisCache
import os
import unittest
from py_redis_cache import RedisCache, Singleton
from redis.exceptions import ConnectionError


class TestRedisCacheConnection(unittest.TestCase):

    def test_connect_via_host_port(self):
        # Disable Singleton for testing
        Singleton.disable = True
        redis_cache = RedisCache(host="127.0.0.1", port=6379)
        assert redis_cache.client.ping() is True

    def test_connect_via_host_port_wrong(self):
        # Redis does not listening on port 6380
        Singleton.disable = True
        redis_cache = RedisCache(
            host="127.0.0.1",
            port=99999,
        )
        self.assertRaises(
            ConnectionError,
            redis_cache.client.ping
        )

    def test_connect_via_url(self):
        Singleton.disable = True
        redis_cache = RedisCache(redis_url="redis://127.0.0.1:6379")
        assert redis_cache.client.ping() is True

    def test_connect_via_env(self):
        Singleton.disable = True
        os.environ["REDIS_URL"] = "redis://127.0.0.1:6379"
        # Provide incorrect host, port to demostrate passing redis_url via Env possible
        redis_cache = RedisCache(host="fakehost", port=1)
        os.environ["REDIS_URL"] = "" # Reset
        assert redis_cache.client.ping() is True

        os.environ["REDIS_CACHE_URL"] = "redis://127.0.0.1:6379"
        # Provide incorrect host, port to demostrate passing redis_url via Env possible
        redis_cache = RedisCache(host="fakehost", port=1)
        os.environ["REDIS_CACHE_URL"] = "" # Reset
        assert redis_cache.client.ping() is True


if __name__ == '__main__':
    unittest.main()