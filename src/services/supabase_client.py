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

def insert_room_data():
    """Insert a room into the database.
        use this only when you are required to create a new room, it will create a room with NULL values in the database
        if also required to insert data into room, then first create room using this function,
        next call update_room_data tool to update NULL values with real values
        
    """
    response = (supabase.table("rooms")
        .insert({
            "occupied_status": False,
        })
        .execute())
    return response


