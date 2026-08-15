from supabase import Client

# Database functions go here

def get_namespacename_from_supabase(client: Client, user_id):
    response = (client.table("pinecone_data_table")
                .select("namespace_name")
                .eq("business_id", user_id)
                .execute())
    # if response is None, raise error
    namespace_name = ""
    if response is not None and response.data:
        namespace_name = response.data[0]["namespace_name"]
    return namespace_name

def get_thread_id_from_supabase(client: Client, user_id):
    response = (client.table("links")
                .select("thread_id")
                .eq("business_id", user_id)
                .execute()
                )
    thread_id = ""
    if response is not None and response.data:
        thread_id = response.data[0]["thread_id"]
    return thread_id

def get_published_status_from_supabase(client: Client, user_id):
    response = (client.table("links")
                .select("published")
                .eq("business_id", user_id)
                .execute()
                )
    published = False
    if response is not None and response.data:
        published = response.data[0]["published"]
    return published

def set_published_status_in_supabase(client: Client, user_id, published: bool):
    response = (client.table("links")
                .update({"published": published})
                .eq("business_id", user_id)
                .execute()
                )
    if response is None or not response.data:
        raise ValueError(f"No links row found for user {user_id}")
    return response.data[0]["published"]

def get_slots_from_supabase(client: Client, user_id):
    response = (client.table("slots")
                .select("*")
                .eq("business_id", user_id)
                .execute()
                )
    slots = []
    if response is not None and response.data:
        slots = response.data
    return slots

def get_url_from_supabase(client: Client, user_id):
    response = (client.table("links")
                    .select("url")
                    .eq("business_id", user_id)
                    .execute()
                    )
    url= ""
    if response is not None and response.data:
        url= response.data[0]["url"]
    return url

def get_publish_status_from_supabase(client: Client, user_id):
    response = (client.table("links")
                .select("published")
                .eq("business_id", user_id)
                .execute()
                )
    status = False
    if response is not None and response.data:
        status = response.data[0]["published"]
    return status
