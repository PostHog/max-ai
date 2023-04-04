import os
import re
from typing import List

import slack # noqa
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from haystack import Document
from pydantic import BaseModel
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from weaviate.util import generate_uuid5

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

# FastAPI App

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Slack Bolt App

slack_app = App()
app_handler = SlackRequestHandler(slack_app)

class Entry(BaseModel):
    content: str
    meta: dict

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
        headings = split_markdown_sections(entry.content)

        documents = [Document(id=generate_uuid5(doc), content=doc, content_type='text', meta=entry.meta) for doc in headings if doc]
        pipeline.embed_documents(documents)

    pipeline.update_embeddings()

    return []

@app.post("/spawn")
def receive_spawn():
    print("Spawned")
    return []

@app.post("/chat")
def chat(messages: List[Message]):
    msgs = [msg.dict() for msg in messages]
    print(msgs)
    response = ai_chat_thread(msgs)
    return response

@app.get("/_health")
def health():
    return {"status": "ok"}

@app.post("/slack/events")
async def slack_events(req: Request):
    return await app_handler.handle(req)

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

