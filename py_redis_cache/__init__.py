import pickle
import json
import logging
import os
from redis import Redis
from typing import Callable, Iterable, Union, Tuple
from .utils import make_key


# Specical key to avoid conflict with args while
# filtering cache keys, use numeric since args can't start with
TAG_KEY = "00"
FUNC_KEY = "11"
SEP = "="

current_redis_cache = None
current_aio_redis_cache = None

class Singleton(type):
    disable = False
    _instances = {}
    def __call__(cls, *args, **kwargs):
        from .asyncio import AsyncRedisCache
        global current_redis_cache, current_aio_redis_cache
        is_aio_redis = isinstance(cls, AsyncRedisCache)

        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            if not is_aio_redis:
                current_redis_cache = cls._instances[cls]
            else:
                current_aio_redis_cache = cls._instances[cls]
            
        if cls.disable:
            return cls._instances.pop(cls)
        return cls._instances[cls]
    
    @classmethod
    def clear_instance(cls):
        cls._instances = {}


class RedisCache(metaclass=Singleton):
    """
    RedisCache using Redis for storing data

    Args:
        namespace (str): Namespace of the cache, used as prefix for cache keys
            to avoid possible conflicting.
        serializer (str, default='pickle'): serializer used to serialize data before sending
            to redis, can be `'pickle'` or `'json'`.
        local_cache (bool, default=False): To enable caching on local memory.
        verbose(int, default=0): If set to be greater than `0`, will log in every
            cache added and hitted, can be used for debugging purposes
        logger (logging.Logger, default=None): Logger to log when verbose > 0
        -----
        *args, **kwargs: Can be any arguments you can pass to Redis class
        See: https://github.com/redis/redis-py/blob/07fc339b4a4088c1ff052527685ebdde43dfc4be/redis/client.py#L92

    ### Example

    ```python
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
    """
    redis_cls = Redis

    def __init__(
        self,
        namespace: str = None,
        serializer: str = 'pickle',
        local_cache: bool = False,
        verbose: int = 0,
        logger: logging.Logger = None,
        *args,
        **kwargs
    ) -> None:
        if namespace is None:
            namespace = 'redis_cache'

        self.local_cache = local_cache
        self.__data = {}  # Consider using OrderedDict
        self.serializer = self._get_serializer(serializer)
        self.namespace = namespace
        self.verbose = verbose
        self.client = self._connect(*args, **kwargs)
        self.logger = self._init_logger(logger)

    def _connect(self, *args, **kwargs):
        redis_url = None
        # Try to obtain redis_url from kwargs or environment variable
        redis_url = kwargs.pop("redis_url", None)
        if not redis_url:
            redis_url = os.environ.get("REDIS_CACHE_URL")
        if not redis_url:
            redis_url = os.environ.get("REDIS_URL")
        
        if redis_url:
            return self.redis_cls.from_url(redis_url)
        else:
            return self.redis_cls(*args, **kwargs)

    def _init_logger(
        self,
        logger=None,
        level=None,
        handlers=None
    ) -> logging.Logger:
        if logger is None:
            logger = logging.getLogger("RedisCache")
        if level is None:
            level = logging.INFO
        if handlers is None:
            handlers = [logging.StreamHandler()]

        for handler in handlers:
            logger.addHandler(handler)
        logger.setLevel(level)
        return logger

    def _get_serializer(self, serializer: Union[str, Callable]):
        if isinstance(serializer, str):
            try:
                serializers = {
                    'pickle': pickle,
                    'json': json
                }
                serializer = serializers[serializer]
            except KeyError:
                raise ValueError(
                    f"Unknown serializer {serializer}, support {serializers.keys()}"
                )
        else:
            if not hasattr(serializer, 'loads'):
                raise ValueError(f"Serializer must have `loads` method")
            if not hasattr(serializer, 'dumps'):
                raise ValueError(f"Serializer must have `dumps` method")
            
        return serializer

    def _build_key(
        self,
        tags: Union[list, str],
        func: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Create key string to store and access in redis
        
        The key will be a combination of namespace,
        tags, function name and parameters
        """
        if tags is not None:
            if not isinstance(tags, (tuple, list)):
                tags = [tags]
            prefix = ":".join((f"{TAG_KEY}{SEP}{t}" for t in tags))
        else:
            prefix = ""
        func_key = make_key(func, *args, **kwargs)
        key = f"{self.namespace}:{prefix}:{FUNC_KEY}{SEP}{func_key}"
        # key = key.encode("utf-8")
        return key

    def log_info(self, msg):
        """Call logger.info if verbose is on"""
        if self.verbose:
            self.logger.info(msg)

    def serialize(self, value):
        """Serialize data before storing in Redis"""
        return self.serializer.dumps(value)
    
    def deserialize(self, value):
        """Deserialize data received from Redis,
        actually inverse of ``serialize``"""
        return self.serializer.loads(value)

    def setex(self, key, value, ttl):
        if self.local_cache:
            # Store data into local cache
            self.__data[key] = value

        data = self.serialize(value)
        self.log_info(f"Cache added, key={key}, size={(len(data) / 1e6):.3f}Kb")
        return self.client.set(key, data, ttl)

    def get(self, key):
        """Get item from cache"""
        data = None
        if self.local_cache:
            # Try to get from local cache first
            data = self.__data.get(key)
            if data is not None:
                # Return here, dont need to deserialize
                return data

        data = self.client.get(key)
        if data is not None:
            data = self.deserialize(data)
        return data

    def scan_iter(self, keyword: str) -> Iterable:
        """Get list of keys from given tag
        be notice that this operation complexity is `O(N)`
        """
        return self.client.scan_iter(keyword)
    
    def find_by_func(self, func: Union[Callable, str]) -> Iterable:
        if callable(func):
            func = func.__module__.__qualname__
            q = f"*:{FUNC_KEY}{SEP}{func}*"
        else:
            # Just func name, need to scan every that between
            # SEP and func name to match module
            q = f"*:{FUNC_KEY}{SEP}*.{func}*"
        return self.scan_iter(q)

    def find_by_tag(self, tag: str) -> Iterable:
        q = f"*:{TAG_KEY}{SEP}{tag}"
        return self.scan_iter(q)

    def delete_by_func(self, func: Union[Callable, str]):
        """Delete cache key by func name
        The keys will be obtained from `find_by_func`
        """
        for key in self.find_by_func(func):
            self.client.delete(key)

    def delete_by_tag(self, tag: str):
        """Delete cache key by tag
        The keys will be obtained from `find_by_tag`
        """
        for key in self.delete_by_tag(tag):
            self.client.delete(key)

    def cache(
        self,
        tags: Union[list, str] = None,
        ttl=30
    ) -> Callable:
        """
        Return a decorator to cache the output of a function.
        The cache will be invalidated after amount of time defined by
        `ttl` argument (30 seconds by default)

        Args:
            tags(list|str, optional): tag of the cache, the tag 
                will be added to the key for storing data.
            ttl(int): Time to live of the cache, that mean the cache
                will be deleted after `ttl` seconds.

        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                key = self._build_key(tags, func, *args, **kwargs)
                data = self.get(key)
                if data is None:
                    # Cache miss, call function and set result in redis
                    data = func(*args, **kwargs)
                    self.setex(key, data, ttl=ttl)
                else:
                    # Cache hit
                    self.log_info(f"Cache hit, key={key}")
                return data
            return wrapper
        return decorator
