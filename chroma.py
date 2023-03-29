import os
from chromadb.utils import embedding_functions
import chromadb


client = chromadb.Client()

def get_collection(collection_name):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("OPENAI_TOKEN"),
        model_name="text-embedding-ada-002"
    )
    
    try:
        collection = client.create_collection(collection_name, embedding_function=openai_ef)
    except:
        collection = client.get_collection(collection_name)

    return collection