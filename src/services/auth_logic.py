"""Signup/login against Supabase Auth (GoTrue).

Raw passwords are forwarded to Supabase and nothing else: GoTrue stores them
bcrypt-hashed on its side, so this layer never persists, logs or returns one.
The route layer stays thin by catching AuthenticationError, which already
carries the status code Supabase reported.
"""

from supabase import AuthApiError, AuthError
from services.supabase_client import create_auth_client
from utils.exceptions import AuthenticationError
from fastapi import Request

def _serialize_user(user):
    """Trim the GoTrue user down to what a client is allowed to see."""
    # sign_up/sign_in can both hand back user=None, so callers get None rather than a crash
    if user is None:
        return None
    return {
        "id": str(user.id),
        "email": user.email,
        "created_at": str(user.created_at) if user.created_at else None,
        "email_confirmed_at": str(user.email_confirmed_at) if user.email_confirmed_at else None,
    }
    # everything else on the GoTrue user (identities, app_metadata, user_metadata,
    # phone, ...) is deliberately dropped - the browser has no use for it


def _serialize_session(session):
    # no session means "not logged in"; see sign_up for the case where that is normal
    if session is None:
        return None
    return {
        # the JWT the frontend sends back as `Authorization: Bearer <token>`
        "access_token": session.access_token,
        # used to mint a fresh access_token once the one above expires
        "refresh_token": session.refresh_token,
        "token_type": session.token_type,
        # unix timestamp - lets the client refresh before it is rejected
        "expires_at": session.expires_at,
    }

def check_session_exists(req: Request):
    """FastAPI dependency: verify the caller's bearer token against Supabase.

    Protected routes take this as a `Depends(...)` and get the serialized user
    back, so the handler never touches the raw token. Anything that is not a
    live session raises AuthenticationError; main.py turns that into the right
    HTTP status, because a dependency runs *before* the route body and so cannot
    be covered by the per-route try/except that /auth uses.
    """
    header = req.headers.get("Authorization", "")
    # scheme is case-insensitive per RFC 6750; the token itself is not
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != "bearer" or not token:
        raise AuthenticationError("Missing bearer token", status_code=401)

    # per-call client: get_user sends the caller's JWT, and that identity must not
    # stick to the shared client afterwards (see create_auth_client)
    supabase = create_auth_client()
    try:
        # asks GoTrue instead of decoding the JWT locally, so a session that was
        # revoked or a user that was deleted is rejected now rather than staying
        # trusted until the token's own expiry
        response = supabase.auth.get_user(token)
    except AuthApiError as e:
        # expired, malformed, revoked - all 401 to the client whatever GoTrue called it
        raise AuthenticationError(e.message, status_code=401) from e
    except AuthError as e:
        raise AuthenticationError(str(e), status_code=401) from e
    except Exception as e:
        # network/config failure - ours, not the caller's
        raise AuthenticationError(f"Session check failed: {e}", status_code=500) from e

    # get_user returns None when it had no jwt to work with, and a UserResponse can
    # still carry user=None; neither is a session
    if response is None or response.user is None:
        raise AuthenticationError("Invalid or expired session", status_code=401)

    return {**(_serialize_user(response.user)), "access_token": token}

def sign_up(email: str, password: str):
    """Register a new user.

    Supabase returns a user with no session when the project has email
    confirmation turned on, so that case is reported rather than mistaken for a
    failed signup.
    """
    # per-call client: signing up must not leave a session on the shared client
    supabase = create_auth_client()
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
    except AuthApiError as e:
        # GoTrue rejected it for a known reason (email taken, password too weak, ...);
        # e.status is the HTTP code it used, which we pass through unchanged
        raise AuthenticationError(e.message, status_code=e.status or 400) from e
    except AuthError as e:
        raise AuthenticationError(str(e)) from e
    except Exception as e:
        # network/config failure - ours, not the caller's, so 500
        raise AuthenticationError(f"Sign up failed: {e}", status_code=500) from e

    # a 2xx with no user should not happen, but returning None to the route would
    # surface as a confusing 200 with an empty body
    if response.user is None:
        raise AuthenticationError("Sign up did not return a user", status_code=400)

    return {
        "user": _serialize_user(response.user),
        # present only when email confirmation is off, i.e. the user is auto-logged-in
        "session": _serialize_session(response.session),
        # tells the frontend whether to show "check your inbox" or go straight in
        "requires_email_confirmation": response.session is None,
    }


def sign_in(email: str, password: str):
    """Exchange credentials for an access/refresh token pair."""
    # per-call client, so this login's JWT does not become the process-wide identity
    supabase = create_auth_client()
    try:
        # GoTrue re-hashes the given password and compares it against the stored hash
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    except AuthApiError as e:
        # GoTrue answers 400 for bad credentials; 401 is the honest code for a client.
        # Anything else it reports (429 rate limit, 403 banned user) is kept as-is.
        status_code = 401 if e.status in (None, 400) else e.status
        raise AuthenticationError(e.message, status_code=status_code) from e
    except AuthError as e:
        raise AuthenticationError(str(e), status_code=401) from e
    except Exception as e:
        # network/config failure rather than a rejected login
        raise AuthenticationError(f"Login failed: {e}", status_code=500) from e

    # unlike sign_up, a login with no session is never legitimate
    if response.session is None:
        raise AuthenticationError("Invalid email or password", status_code=401)

    return {
        "user": _serialize_user(response.user),
        "session": _serialize_session(response.session),
    }
