from redis.asyncio import Redis
import asyncio
from app.config.redis import r

''' 
    This is a background worker running for every 5 sec refreshing the arena, by adding users into it
    Using hashes we set expiration time for the user which should update in the frontend too (later)
'''

async def worker():
    
    q = "VirtualQueue"

    print("Worker running for every 5 secs!!")
    while True:

        try:
            users = await r.zpopmin(q, 10)
            for user, score in users:
                print(f"Inserting user : {user}")
                
                user_data = {"in_arena": "1"} # user moves to arena to book tickets and reserve
                await r.hset(f'user:{user}', mapping=user_data)

                # Set expiration time (12 minutes)
                await r.expire(f'user:{user}', 720)
                print('Inserted and set TTL')

        except Exception as e:
            print("Error occured!1")
            print(e)
        
        await asyncio.sleep(5)

asyncio.run(worker())