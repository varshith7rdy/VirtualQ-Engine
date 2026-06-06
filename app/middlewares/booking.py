from redis.asyncio import Redis
from fastapi import Request, Response
from ..config.redis import r
from ..middlewares.auth import get_current_user_id

async def BookingMiddleware(request: Request, call_next):
    
    path = request.url.path

    if path.startswith("/booking") == True:

        user = get_current_user_id(request)
        if not user:
            return Response(content="Invalid user", status_code=400)

        res = await r.hexists(f'user:{user}', 'in_arena')
        if not res:
            return Response(content="Not allowed to book!", status_code=400)
        print(f'User: {user} exists and is allowed to the booking arena')

    response = await call_next(request)
    return response