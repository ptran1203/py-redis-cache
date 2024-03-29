import asyncio
import pickle
import json
import logging
import os
from redis.asyncio import Redis
from typing import Callable, Iterable, Union, Tuple
from .. import RedisCache


# Specical key to avoid conflict with args while
# filtering cache keys, use numeric since args can't start with
TAG_KEY = "00"
FUNC_KEY = "11"
SEP = "="


class AsyncRedisCache(RedisCache):
    """
    RedisCache with asyncio support

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

    async def setex(self, key, value, ttl):
        if self.local_cache:
            # Store data into local cache
            self.__data[key] = value

        data = self.serialize(value)
        self.log_info(f"Cache added, key={key}, size={(len(data) / 1e6):.3f}Kb")
        return await self.client.set(key, data, ttl)

    async def get(self, key):
        """Get item from cache"""
        data = None
        if self.local_cache:
            # Try to get from local cache first
            data = self.__data.get(key)
            if data is not None:
                # Return here, dont need to deserialize
                return data

        data = await self.client.get(key)
        if data is not None:
            data = self.deserialize(data)
        return data

    async def scan_iter(self, keyword: str) -> Iterable:
        """Get list of keys from given tag
        be notice that this operation complexity is `O(N)`
        """
        return await self.client.scan_iter(keyword)
    
    async def find_by_func(self, func: Union[Callable, str]) -> Iterable:
        if callable(func):
            func = func.__module__.__qualname__
            q = f"*:{FUNC_KEY}{SEP}{func}*"
        else:
            # Just func name, need to scan every that between
            # SEP and func name to match module
            q = f"*:{FUNC_KEY}{SEP}*.{func}*"
        return await self.scan_iter(q)

    async def find_by_tag(self, tag: str) -> Iterable:
        q = f"*:{TAG_KEY}{SEP}{tag}"
        return await self.scan_iter(q)

    async def delete_by_func(self, func: Union[Callable, str]):
        """Delete cache key by func name
        The keys will be obtained from `find_by_func`
        """
        async for key in self.find_by_func(func):
            await self.client.delete(key)

    async def delete_by_tag(self, tag: str):
        """Delete cache key by tag
        The keys will be obtained from `find_by_tag`
        """
        async for key in self.delete_by_tag(tag):
            await self.client.delete(key)

    def aio_cache(
        self,
        tags: Union[list, str] = None,
        ttl=30
    ) -> Callable:
        """
        Return a decorator to cache the output of a async function.
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
            async def wrapper(*args, **kwargs):
                key = self._build_key(tags, func, *args, **kwargs)
                data = await self.get(key)
                if data is None:
                    # Cache miss, call function and set result in redis
                    data = await func(*args, **kwargs)
                    await self.setex(key, data, ttl=ttl)
                else:
                    # Cache hit
                    self.log_info(f"Cache hit, key={key}")
                return data
            return wrapper
        return decorator
