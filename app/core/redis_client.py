"""Basic connection example.
"""

import redis.asyncio as redis

redis_client = redis.Redis(
    host='redis-15598.c264.ap-south-1-1.ec2.cloud.redislabs.com',
    port=15598,
    decode_responses=True,
    username="default",
    password="6uHMOeGPByt5oTmWMNUZ5U9dwq8w6BSX",
)

