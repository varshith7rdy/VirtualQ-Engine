from redis.asyncio import Redis
from fastapi import Request, Response
from app.config.redis import r

async def BookingMiddleware(request: Request, call_next):
    
    path = request.url.path

    if path.startswith("/booking") == True:

        user = request.headers.get("X-User-Id") 
        if not user:
            return Response(content="Invalid user", status_code=400)

        print(f'User: {user} exists and is allowed to the booking arena')
        res = await r.hexists(f'user:{user}', 'IP')
        if not res:
            return Response(content="Not allowed to book!", status_code=400)

    response = await call_next(request)
    return response