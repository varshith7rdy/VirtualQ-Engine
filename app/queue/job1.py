from redis.asyncio import Redis
import asyncio
from app.config.redis import r
# Needs db here for writing update query
from app.config.db import session
from app.model import Tickets
from datetime import datetime

'''
    This is a background worker running for every 30 sec refreshing the arena, by updating the ticket status
    which TTL has expired. (Not efficient still works atmost 30-seconds extra for user)
'''

async def worker():
    
    
    while True:

        try:
            db = session()
            print(datetime.now())
            res = db.query(Tickets).filter(
                Tickets.expires_at < datetime.now()
            ).update({
                Tickets.status: "AVAILABLE"
            })
            db.commit()
            print('Successful run!', res)

        except Exception as e:
            print("Error occured!1")
            print(e)
        
        await asyncio.sleep(30) #30 seconds

asyncio.run(worker())