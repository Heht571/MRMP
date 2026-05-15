"""
缓存服务 - 提供简单的内存缓存功能
"""
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps
from collections import OrderedDict


class LRUCache:
    """简单的 LRU 缓存实现"""

    def __init__(self, maxsize: int = 128):
        self.cache: OrderedDict = OrderedDict()
        self.maxsize = maxsize
        self.ttl_map: Dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None

        # 检查 TTL
        if key in self.ttl_map:
            if time.time() > self.ttl_map[key]:
                del self.cache[key]
                del self.ttl_map[key]
                return None

        # 移到末尾（最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                # 删除最旧的
                oldest = next(iter(self.cache))
                del self.cache[oldest]
                self.ttl_map.pop(oldest, None)

        self.cache[key] = value

        if ttl:
            self.ttl_map[key] = time.time() + ttl

    def delete(self, key: str) -> None:
        self.cache.pop(key, None)
        self.ttl_map.pop(key, None)

    def clear(self) -> None:
        self.cache.clear()
        self.ttl_map.clear()

    def size(self) -> int:
        return len(self.cache)


# 全局缓存实例
_model_cache = LRUCache(maxsize=256)
_attribute_cache = LRUCache(maxsize=512)
_relation_def_cache = LRUCache(maxsize=128)


def cached(cache: LRUCache, ttl: int = 300):
    """缓存装饰器

    Args:
        cache: 缓存实例
        ttl: 过期时间(秒)，默认 5 分钟
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝���从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# ============ 便捷方法 ============
async def get_cached_model_attributes(db, model_id: str, fetch_func: Callable):
    """获取缓存的模型属性

    Args:
        db: 数据库会话
        model_id: 模型ID
        fetch_func: 获取数据的异步函数

    Returns:
        模型属性列表
    """
    cache_key = f"model_attributes:{model_id}"
    result = _attribute_cache.get(cache_key)

    if result is None:
        result = await fetch_func(db, model_id)
        _attribute_cache.set(cache_key, result, ttl=300)  # 5分钟

    return result


async def get_cached_model(db, model_id: str, fetch_func: Callable):
    """获取缓存的模型"""
    cache_key = f"model:{model_id}"
    result = _model_cache.get(cache_key)

    if result is None:
        result = await fetch_func(db, model_id)
        _model_cache.set(cache_key, result, ttl=300)

    return result


def invalidate_model_cache(model_id: str = None):
    """清除模型相关缓存

    Args:
        model_id: 如果指定，只清除该模型的缓存；否则清除所有
    """
    if model_id:
        _model_cache.delete(f"model:{model_id}")
        _attribute_cache.delete(f"model_attributes:{model_id}")
    else:
        _model_cache.clear()
        _attribute_cache.clear()


def invalidate_relation_def_cache():
    """清除关系定义缓存"""
    _relation_def_cache.clear()