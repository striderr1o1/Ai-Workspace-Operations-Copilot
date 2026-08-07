import sys
import os
import jwt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
from services.supabase_client import get_supabase_client_with_token
import services.supabase_client
from supabase import Client
#from unittest.mock import patch, Mock


def test_get_supabase_client_with_token():
    payload = {
            "email": "thegreatkodu@email.com",
            "password": "wowbro"
            }
    mock_jwt = jwt.encode(payload, "secret", algorithm="HS256")
    client = get_supabase_client_with_token(mock_jwt)
    assert isinstance(client, Client)


