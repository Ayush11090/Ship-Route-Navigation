import time
from collections import deque
from functools import wraps

class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            now = time.time()
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                print(f"Rate limit reached. Sleeping for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)

            result = await func(*args, **kwargs)
            self.calls.append(time.time())
            return result
        return wrapper

# Initialize rate limiter for weather API (500 calls/minute)
weather_rate_limiter = RateLimiter(500, 60)