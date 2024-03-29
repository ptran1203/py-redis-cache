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
    _instances = {}
    def __call__(cls, *args, **kwargs):
        from .asyncio import AsyncRedisCache
        global current_redis_cache, current_aio_redis_cache
        is_aio_redis = isinstance(cls, AsyncRedisCache)

        if cls not in cls._instances:
            
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            if is_aio_redis:
                current_redis_cache = cls._instances[cls]
                print("SET", current_redis_cache)
            else:
                current_aio_redis_cache = cls._instances[cls]
                print("SET AIO", current_aio_redis_cache)
        return cls._instances[cls]


class RedisCache(metaclass=Singleton):
    """
    RedisCache using Redis for storing data

    Args:
        namespace (str):
        serializer (str):
        local_cache (bool):
        verbose(int):
        logger (logging.Logger):

    # Usage

    # Example
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


def cached(
    cache_instance: RedisCache,
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
            key = cache_instance._build_key(tags, func, *args, **kwargs)
            data = cache_instance.get(key)
            if data is None:
                # Cache miss, call function and set result in redis
                data = func(*args, **kwargs)
                cache_instance.setex(key, data, ttl=ttl)
            else:
                # Cache hit
                cache_instance.log_info(f"Cache hit, key={key}")
            return data
        return wrapper
    return decorator
