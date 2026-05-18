from .supabase_client import get_supabase_client
#from argon2 import PasswordHasher
supabase = get_supabase_client()
#ph = PasswordHasher(
#        hash_len=8
#        )
# need to implement authentication using supabase
#def hash_password(password: str):
#    hashed_pw = ph.hash(password)
#    return hashed_pw

def signup(email: str, password: str):
    response = supabase.auth.sign_up(
    {
        "email": email,
        "password": password,
    }
    )
    return response

def signin():
    response = supabase.auth.sign_in_with_oauth(
    {"provider": "google"}
    )
    return response

def signout():
    return
