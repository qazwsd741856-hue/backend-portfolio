import redis
from redis.retry import Retry
from redis.backoff import NoBackoff

redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry=Retry(NoBackoff(),0)
)