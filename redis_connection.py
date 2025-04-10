import redis
import json

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_session(user_id: str):
    key = f"session:{user_id}"
    session = r.get(key)
    return json.loads(session) if session else {}

def save_session(user_id: str, data: dict, ttl_seconds=7*24*3600):
    key = f"session:{user_id}"
    r.setex(key, ttl_seconds, json.dumps(data))
