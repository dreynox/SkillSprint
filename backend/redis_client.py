import redis
from config import REDIS_URL, REDIS_SOCKET_CONNECT_TIMEOUT, REDIS_SOCKET_TIMEOUT

# Create a connection pool for Redis
pool = redis.ConnectionPool.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=REDIS_SOCKET_CONNECT_TIMEOUT,
    socket_timeout=REDIS_SOCKET_TIMEOUT
)

def get_redis_client() -> redis.Redis:
    """Returns a Redis client using the connection pool."""
    return redis.Redis(connection_pool=pool)
