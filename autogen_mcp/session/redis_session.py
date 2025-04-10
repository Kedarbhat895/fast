import redis
import json

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def get_session(user_id):
    key = f"session:{user_id}"
    val = r.get(key)
    return json.loads(val) if val else {}

def save_session(user_id, data, ttl_seconds=7*24*3600):
    key = f"session:{user_id}"
    r.setex(key, ttl_seconds, json.dumps(data))
