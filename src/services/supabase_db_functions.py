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


