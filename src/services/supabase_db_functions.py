from services.supabase_client import get_supabase_client_with_token

# Database functions go here

def get_namespacename_from_supabase(access_tokem: str, user_id):
    client = get_supabase_client_with_token(access_tokem)
    response = (client.table("pinecone_data_table")
                .select("namespace_name")
                .eq("business_id", user_id)
                .execute())
    # if response is None, raise error
    return response
