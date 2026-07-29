"""App-level exception handlers, registered on the FastAPI app in main.py.

These exist for exceptions raised *outside* a route body - dependencies resolve
before the handler runs, so the per-route try/except that routes/auth.py uses
never sees them. Kept out of exceptions.py so that module stays framework-free.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from utils.exceptions import AuthenticationError


async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Turn a rejected session into the status Supabase reported, not a 500.

    `detail` matches the shape HTTPException produces, so the frontend can read
    both this and the /auth routes the same way.
    """
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.text})
