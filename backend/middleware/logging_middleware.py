import time

from fastapi import Request


async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)
    print(f"{request.method} {request.url.path} completed in {process_time}ms")
    return response
