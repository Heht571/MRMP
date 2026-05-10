from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable
import time
from collections import defaultdict

# In-memory rate limiter (use Redis for production)
class RateLimiter:
    def __init__(self):
        self.requests: dict = defaultdict(list)
        self.max_requests = 5  # 5 requests per minute
        self.window = 60  # 60 seconds

    def check(self, key: str) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[key] = [req_time for req_time in self.requests[key] if now - req_time < self.window]

        if len(self.requests[key]) >= self.max_requests:
            return False

        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

async def rate_limit_login(request: Request):
    """Rate limiting for login endpoint - 5 attempts per minute per IP"""
    client_ip = request.client.host if request.client else "unknown"
    key = f"login:{client_ip}"

    if not rate_limiter.check(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录尝试过于频繁，请1分钟后再试"
        )