from dotenv import load_dotenv
load_dotenv()
from google import genai 
from google.genai import types

client = genai.Client()  # reads GOOGLE_API_KEY from env


def get_google_embeddings(chunks):
    result = client.models.embed_content(
          model="gemini-embedding-001",
          contents=chunks,
          config=types.EmbedContentConfig(output_dimensionality=1024),
    )
    embeddings = [e.values for e in result.embeddings]  # one vector per chunk
    return embeddings


# bottle neck: according to claude, if chunks are greater than 100 than google embedding model will reject it so go with batch size
# also need to look up normalization
