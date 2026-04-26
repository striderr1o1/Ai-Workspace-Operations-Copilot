import os
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_apikey = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_apikey)


def fetch_room_data():
    """Fetch room data to check if which rooms are available"""
    response = (supabase.table("rooms")
    .select("*")
    .execute())
    print(response)
    return response

def update_room_data():
    return

def delete_room_data():
    return

def create_room_data():
    return


