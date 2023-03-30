import os
from dotenv import load_dotenv
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from haystack import Document
import re

from ai import ai_chat_thread
from pipeline import MaxPipeline


load_dotenv()  # take environment variables from .env.

origins = [
    "http://localhost",
    "http://localhost:8001",
    "http://localhost:8002",
    "https://app.posthog.com",
    "https://posthog.com",
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Entry(BaseModel):
    id: str
    slug: Optional[str]
    contentHash: str
    body: str

class Entries(BaseModel):
    entries: List[Entry]

class Message(BaseModel):
    role: str
    content: str

pipeline = MaxPipeline(
    openai_token=os.getenv("OPENAI_TOKEN")
)

@app.post("/entries")
def create_entries(entries: Entries):
    for entry in entries.entries:
        headings = split_markdown_sections(entry.body)

        documents = [Document(content=doc) for doc in headings]
        pipeline.embed_documents(documents)

    return []

@app.post("/chat")
def chat(messages: List[Message]):
    msgs = [msg.dict() for msg in messages]
    print(msgs)
    response = ai_chat_thread(msgs)
    return response

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

