from redis.asyncio import Redis
import asyncio

''' 
    This is a background worker running for every 5 sec refreshing the arena, by adding users into it
    Using hashes we set expiration time for the user which should update in the frontend too
'''

async def worker():
    
    r = Redis(host="localhost", decode_responses=True, port=6379)
    q = "VirtualQueue"

    while True:

        try:
            users = await r.zpopmin(q, 10)
            for user, score in users:
                
                print(f"Inserting user : {user}")
                await r.hset(f'user:{user}', mapping={
                    "IP": 1202
                })
                
                # Setting 12 min Time limit
                await r.expire(f'user:{user}', 720)
                print('Inserted and set TTL')

        except Exception as e:
            print("Error occured!1")
            print(e)
        
        await asyncio.sleep(5)

asyncio.run(worker())