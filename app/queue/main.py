from fastapi import FastAPI
from redis.asyncio import Redis
from datetime import datetime
from pydantic import BaseModel
import asyncio

r = Redis(host="localhost", port=6379, decode_responses=True)

q = "VirtualQueue"

class Request(BaseModel):
    name: str

class Update(BaseModel):
    offset: int

app = FastAPI()

@app.post('/queue/join')
async def start(req: Request):
    
    score = datetime.now().timestamp() # scored by the timestamp
    await r.zadd(q, {
        req.name: score    
    })
    return { "msg": "Inserted Successfully" }


@app.get('/queue/ranks')
async def ranks():

    res = await r.zrange(q, 0, -1, withscores=True)
    return {"response": res}

@app.get('/queue/getrank')
async def get_rank(req: Request):

    try:
        
        rank = await r.zrank(q, req.name)

        if(rank == None):
            return {"message": "You aren't in the queue!!"}
        
        res = await r.hget(f'user:{req.name}', 'IP')

        if(res != None):
            return {"message": "Should be redirected to Arena"}
        
    except Exception as e:
        print("Exception occured!!")
        print(e)

    return {"rank": rank, "result": res}


@app.post('/queue/update')
async def update(req: Update):
    val = req.offset
    await r.zremrangebyrank(q, 0, max(val-1, 0))
    res = await r.zrange(q, 0, -1, withscores=True)
    return {"response": res}
    

@app.get('/queue/arenausers')
async def get_arenausers():

    res = await r.keys("user*")

    return { "users": res }
