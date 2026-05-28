from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List
import time
from collections import defaultdict
from fastapi import Request, Response

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit:Dict[str, List[float]] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):

        # Handle case where request.client might be None
        if request.client is None:
            ip = "unknown"
        else:
            ip = request.client.host
            
        current_time = time.time()

        self.rate_limit[ip] = [t for t in self.rate_limit[ip] if current_time - t < 1.0]

        # 5 request per Second
        if len(self.rate_limit[ip]) >= 5:
            return Response(content="Rate Limit Exceeded", status_code=429)
        
        self.rate_limit[ip].append(current_time)

        st_time = time.time()
        response = await call_next(request)
        time_processed = time.time() - st_time

        print(f'Response took {time_processed} secs')

        return response
