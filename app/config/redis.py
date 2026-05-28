import os
from dotenv import load_dotenv
from redis.asyncio import Redis

load_dotenv()
HOST = os.getenv('REDIS_HOST')
PORT = os.getenv('REDIS_PORT')

r = Redis(host=HOST, port=PORT, decode_responses=True)