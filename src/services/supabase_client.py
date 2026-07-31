import os
from supabase import create_client, Client
from supabase.client import ClientOptions
from dotenv import load_dotenv
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_apikey = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_apikey)

def get_supabase_client():
    return supabase

def get_supabase_client_with_token(access_token: str) -> Client:
    """Create a per-request Supabase client authenticated as the given user.

    Sets the session with the caller's JWT so that auth.uid() resolves correctly
    in RLS policies. Each call returns a fresh client; the token does not bleed
    into other requests.
    """
    client = create_client(
        supabase_url,
        supabase_apikey,
        options=ClientOptions(persist_session=False, auto_refresh_token=False),
    )
    client.postgrest.auth(access_token)
    return client

def create_auth_client() -> Client:
    """Build a throwaway client for a single auth call.

    supabase-py stores the signed-in session *on the client instance*, so signing
    a user in through the shared client above would leave every later request in
    this process - room tools included - carrying that user's JWT instead of the
    project key. A per-call client keeps one user's login out of the next
    request. auto_refresh_token is off because these clients are discarded
    immediately and a refresh timer per login would pile up background threads.
    """
    return create_client(
        supabase_url,
        supabase_apikey,
        options=ClientOptions(persist_session=False, auto_refresh_token=False),
    )
