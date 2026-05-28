from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from redis.asyncio import Redis
from datetime import datetime
from pydantic import BaseModel
import time
from dotenv import load_dotenv
import asyncio
from middlewares.ratelimiter import RateLimiter
from middlewares.booking import BookingMiddleware
import os
from app.config.redis import r

load_dotenv()

q = "VirtualQueue"

class JoinRequest(BaseModel):
    name: str

class UpdateRequest(BaseModel):
    offset: int

app = FastAPI()


# Middlewares
app.add_middleware(RateLimiter)

@app.middleware("http")
async def booking_http_middleware(request: Request, call_next):
    return await BookingMiddleware(request, call_next)


# Endpoints
@app.post('/queue/join')
async def start(req: Request):

    user = req.headers.get("X-User-Id")
    score = datetime.now().timestamp() # scored by the timestamp
    await r.zadd(q, {
        user: score
    })
    return { "msg": "Inserted Successfully" }


@app.get('/queue/ranks')
async def ranks():

    res = await r.zrange(q, 0, -1, withscores=True)
    return {"response": res}

@app.get('/queue/getrank')
async def get_rank(req: Request):

    try:

        name = req.headers.get('X-User-Id')
        
        rank = await r.zrank(q, name)

        if rank is None:
            return {"message": "You aren't in the queue!!"}
        
        res = r.hget(f'user:{name}', 'IP')

        if res is not None:
            return {"message": "Should be redirected to Arena"}

    except Exception as e:
        print("Exception occured!!")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"rank": rank, "result": res}


@app.post('/queue/update')
async def update(req: UpdateRequest):

    val = req.offset
    await r.zremrangebyrank(q, 0, max(val-1, 0))
    res = await r.zrange(q, 0, -1, withscores=True)
    return {"response": res}
    

@app.get('/queue/arenausers')
async def get_arenausers():

    res = await r.keys("user*")

    return { "users": res }


# Mock endpoint
@app.get("/booking/reserve-seat/")
async def reserve_seat(req: Request):
    
    user = req.headers.get('X-User-Id')
    print(f'User: {user} has booked the seat')
    return Response(content="Successful booking")
