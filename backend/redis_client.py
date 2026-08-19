import redis
from config import REDIS_URL

# Create a connection pool for Redis
pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

def get_redis_client() -> redis.Redis:
    """Returns a Redis client using the connection pool."""
    return redis.Redis(connection_pool=pool)
