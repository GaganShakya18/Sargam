from fastapi import HTTPException, Request, status


async def auth_middleware(request: Request, call_next):
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return await call_next(request)

    if request.url.path.startswith("/api/auth") or request.url.path in {"/", "/health"}:
        return await call_next(request)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )
