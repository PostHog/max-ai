from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import marko
from marko.inline import RawText, StrongEmphasis as Strong, Emphasis, Link
from .chroma import get_collection

load_dotenv()  # take environment variables from .env.

app = FastAPI()

class Entry(BaseModel):
    id: str
    slug: str
    rawBody: str

class Entries(BaseModel):
    entries: List[Entry]

@app.post("/entries")
def create_entries(entries: Entries):
    posthog_collection = get_collection("posthog")
    for entry in entries.entries:
        ps = extract_markdown_paragraphs(entry.rawBody)
        for index, p in enumerate(ps):
            if p:
                posthog_collection.add(
                    documents=[p],
                    ids=[entry.id + f"-{index}"]
                )

    return []

@app.get("/search")
def search_entries(query: str):
    posthog_collection = get_collection("posthog")
    results = posthog_collection.query(
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
