import logging

from redis.exceptions import RedisError
from redis_client import redis_client

logger = logging.getLogger(__name__)

def delete_product_cache(product_id: int):
    try:
        redis_client.delete(f"product:{product_id}")
    except RedisError:
        logger.warning(
            "Redis 目前無法清除商品快取 product:%s",
            product_id
        )