import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
import marko
from marko.block import Heading, Paragraph
from marko.inline import RawText, StrongEmphasis as Strong, Emphasis, Link

load_dotenv()  # take environment variables from .env.
app = FastAPI()

class Entry(BaseModel):
    # title: str
    slug: str
    rawBody: str

class Entries(BaseModel):
    entries: List[Entry]

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/entries/")
def create_entries(entries: Entries):
    for entry in entries.entries:
        ps = extract_markdown_paragraphs(entry.rawBody)
        print(ps)

    return []

def extract_markdown_paragraphs(markdown_str):
    def to_markdown(element):
        if hasattr(element, 'children'):
            return ''.join(to_markdown(child) for child in element.children)
        elif isinstance(element, RawText):
            print("RawText", element)
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
            markdown_paragraph = to_markdown(node)
            paragraphs.append(markdown_paragraph)

    return paragraphs
