import os 
import redis.asyncio as redis
from redis.retry import Retry
from redis.backoff import NoBackoff

REDIS_HOST=os.getenv("REDIS_HOST","redis")
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=6379,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry=Retry(NoBackoff(),0)
)

def get_redis():
    return redis_client

RATE_LIMIT_SCRIPT="""
local count = redis.call("INCR",KEYS[1])

if count == 1 then
    redis.call("EXPIRE",KEYS[1],ARGV[1])
end

local ttl = redis.call("TTL",KEYS[1])

return {count,ttl}
"""