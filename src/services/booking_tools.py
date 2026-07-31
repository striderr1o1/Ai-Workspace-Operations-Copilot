from langchain_core.tools import ToolException
from langchain.tools import tool
from langchain_core.runnables.config import RunnableConfig
from services.supabase_client import get_supabase_client

supabase = get_supabase_client()

@tool
def fetch_room_data(config: RunnableConfig):
    """Fetch all slots/rooms belonging to the current user's business."""
    try:
        user_id = config["configurable"]["user_id"]
        response = (supabase.table("slots")
        .select("*")
        .eq("business_id", user_id)
        .execute())
        return response
    except Exception as e:
        raise ToolException(f"Error in tool execution: {e}")

@tool
def update_room_data(json_object: dict, config: RunnableConfig):
    """Update a slot/room in the database.

    The json_object dict must contain:
        - slotid (uuid): primary key, required to identify which slot to update
        - time_start (timestamptz): reservation start datetime
        - time_end (timestamptz): reservation end datetime
        - occupier_email (citext): email of the person occupying the slot

    Only the fields present in json_object will be updated.
    """
    try:
        user_id = config["configurable"]["user_id"]
        slotid = json_object.pop("slotid")
        response = (supabase.table("slots")
                    .update(json_object)
                    .eq("slotid", slotid)
                    .eq("business_id", user_id)
                    .execute())
        return response
    except Exception as e:
        raise ToolException(f"Error in tool execution: {e}")

@tool
def delete_room_data(slot_id: int, config: RunnableConfig):
    """Delete a slot/room from the database by its id.

    Args:
        slot_id: the id of the slot to delete
    """
    #try:
    #    user_id = config["configurable"]["user_id"]
    #    response = (supabase.table("slots")
    #        .delete()
    #        .eq("id", slot_id)
    #        .eq("business_id", user_id)
    #        .execute())
    #    return response
    #except Exception as e:
    #    raise ToolException(f"Error in tool execution: {e}")
    return

@tool
def insert_room_data(time_start: str, time_end: str, occupier_email: str, config: RunnableConfig):
    """Insert a new slot/room into the database.

    Args:
        time_start: reservation start datetime (ISO 8601 string, e.g. '2026-07-31T09:00:00+00:00')
        time_end: reservation end datetime (ISO 8601 string)
        occupier_email: email of the person occupying the slot
    """
    try:
        user_id = config["configurable"]["user_id"]
        response = (supabase.table("slots")
            .insert({
                "business_id": user_id,
                "time_start": time_start,
                "time_end": time_end,
                "occupier_email": occupier_email,
            })
            .execute())
        return response
    except Exception as e:
        raise ToolException(f"Error in tool execution: {e}")
