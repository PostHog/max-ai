import os
import uuid

import requests
from haystack import Document
from dotenv import load_dotenv
from weaviate.util import generate_uuid5

from pipeline import MaxPipeline, split_markdown_sections

load_dotenv()  # take environment variables from .env.


pipeline = MaxPipeline(
    openai_token=os.getenv("OPENAI_TOKEN")
)


def get_uuid(content):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, content))


def get_sample_doc():
    content = {
        "content": "sample text",
        "slug": "sample-slug",
        "type": "tutorials",
    }
    body = {
        "entries": [
            {
                "id": get_uuid(content["content"]),
                "content": content["content"],
                "meta": {
                    "slug": content["slug"],
                    "type": content["type"],
                },
            }
        ]
    }
    return body


def embed_docs_with_api(docs):
    client = requests.Session()
    host = os.environ.get("MAX_URL", "http://localhost:8000")
    r = client.post(json=docs, url=f"{host}/entries")
    if r.status_code != 200:
        print(docs)
        print(r.text)


def embed_docs_directly(docs):
    for entry in docs['entries']:
        headings = split_markdown_sections(entry['content'])

        documents = [Document(id=generate_uuid5(doc), content=doc, content_type='text', meta=entry['meta']) for doc in headings if doc]
        pipeline.embed_documents(documents)

    pipeline.update_embeddings()

    return []


def seed_sample_doc():
    docs = get_sample_doc()
    embed_docs_directly(docs)


if __name__ == "__main__":
    seed_sample_doc()