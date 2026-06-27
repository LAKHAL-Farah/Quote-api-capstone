import redis
import json 
import os
import random



r= redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=6379,
    decode_responses=True,
)

BASE_TTL_SECONDS = 300
JITTER_SECONDS= 30

def get_cached_quote(quote_id: int):
    try:
        cached = r.get(f"quote:{quote_id}")
    except redis.RedisError:
        return None
    if cached:
        return json.loads(cached)
    return None


def set_cached_quote(quote_id:int, quote_data:dict):
    ttl =BASE_TTL_SECONDS +  random.randint(-JITTER_SECONDS, JITTER_SECONDS)
    try:
        r.set(f"quote:{quote_id}", json.dumps(quote_data),ex=ttl)
    except redis.RedisError:
        return

def invalidate_quote_cache (quote_id:int):
    try:
        r.delete(f"quote:{quote_id}")
    except redis.RedisError:
        return