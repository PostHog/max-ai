from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from .chroma import get_collection
import re

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
    collection = get_collection("posthog")
    for entry in entries.entries:
        headings = split_markdown_sections(entry.rawBody)
        collection.add(
            documents=headings,
            ids=[entry.id + "-" + str(i) for i in range(len(headings))],
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

def split_markdown_sections(markdown_content):
    header_pattern = re.compile(r"(^#+\s+.*$)", re.MULTILINE)
    sections = []

    matches = list(header_pattern.finditer(markdown_content))
    if not matches:
        return [markdown_content]

    for i, match in enumerate(matches[:-1]):
        section_start = match.start()
        section_end = matches[i + 1].start()
        sections.append(markdown_content[section_start:section_end].strip())

    sections.append(markdown_content[matches[-1].start():].strip())

    return sections
