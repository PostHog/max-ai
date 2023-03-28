import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import marko
from marko.inline import RawText, StrongEmphasis as Strong, Emphasis, Link
from chromadb.utils import embedding_functions
import chromadb


load_dotenv()  # take environment variables from .env.

client = chromadb.Client()

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model_name="text-embedding-ada-002"
            )

collection = client.create_collection("posthog", embedding_function=openai_ef) 

app = FastAPI()

class Entry(BaseModel):
    id: str
    slug: str
    rawBody: str

class Entries(BaseModel):
    entries: List[Entry]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/entries")
def create_entries(entries: Entries):
    for entry in entries.entries:
        ps = extract_markdown_paragraphs(entry.rawBody)
        for index, p in enumerate(ps):
            if p:
                collection.add(
                    documents=[p],
                    ids=[entry.id + f"-{index}"]
                )

    return []

@app.get("/search")
def search_entries(query: str):
    results = collection.query(
        query_texts=[query],
        n_results=10,
        
    )
    return results


def extract_markdown_paragraphs(markdown_str):
    def to_markdown(element):
        if isinstance(element, list):
            return ''.join(to_markdown(child) for child in element)
        elif isinstance(element, RawText):
            return element.children
        elif isinstance(element, Strong):
            return f"**{to_markdown(element.children)}**"
        elif isinstance(element, Emphasis):
            return f"*{to_markdown(element.children)}*"
        elif isinstance(element, Link):
            return f"[{to_markdown(element.children)}]({element.dest})"
        else:
            return ''

    marko_doc = marko.parse(markdown_str)
    paragraphs = []

    for node in marko_doc.children:
        if isinstance(node, marko.block.Paragraph):
            markdown_paragraph = to_markdown(node.children)
            paragraphs.append(markdown_paragraph)

    return paragraphs
