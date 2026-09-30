import logging

from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

async def delete_product_cache(redis_client,product_id: int):
    try:
        await redis_client.delete(f"product:{product_id}")
    except RedisError:
        logger.warning(
            "Redis 目前無法清除商品快取 product:%s",
            product_id
        )