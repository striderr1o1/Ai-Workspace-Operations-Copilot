import os
from langchain_core.tools import ToolException
from langchain.tools import tool
from supabase import create_client, Client
from dotenv import load_dotenv
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_apikey = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_apikey)

def get_supabase_client():
    return supabase

@tool
def fetch_room_data():
    """Fetch room data to check if which rooms are available"""
    try:
        response = (supabase.table("rooms")
        .select("*")
        .execute())
        return response
    except Exception as e:
        raise ToolException(f"Error in tool execution: {e}")

@tool
def update_room_data(Json_object):
    """Update room data in the database.

    The json parameter must match the 'rooms' table schema:
        - room_id (int4): primary key, required to identify which room to update
        - occupier_name (text): name of the person occupying the room
        - occupied_status (bool): whether the room is currently occupied
        - start_time (time): reservation start time
        - end_time (time): reservation end time
        - reservation_date (date): date of the reservation
    """
    try:
        response = (supabase.table('rooms')
                    .upsert(Json_object)
                    .execute())
        return response
    except Exception as e:
        raise ToolException(f"Error in tool execution: {e}")

def delete_room_data():
    return

@tool
def insert_room_data():
    """Insert a room into the database.
        use this only when you are required to create a new room, it will create a room with NULL values in the database
        if also required to insert data into room, then first create room using this function,
        next call update_room_data tool to update NULL values with real values
        
    """
    try:
        response = (supabase.table("rooms")
            .insert({
                "occupied_status": False,
            })
            .execute())
        return response
    except Exception as e:
        raise ToolException(f"Error in tool execution: {e}")

#can add langsmith tool server
