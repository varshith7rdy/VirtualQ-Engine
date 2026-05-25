# Docs code

import asyncio
from redis import Redis


r = Redis(host="localhost", port=6379, decode_responses=True)

Queue = "VQ"

res1 = r.zadd("racer_scores", {"Norem": 10})
print(res1)

res2 = r.zadd("racer_scores", {"Castilla": 12})
print(res2) 

res3 = r.zadd(
    "racer_scores",
    {"Sam-Bodden": 8, "Royce": 10, "Ford": 6, "Prickett": 14, "Castilla": 12},
)

print(r.zrevrange("racer_scores", 0, -1, withscores=True))