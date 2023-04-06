import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from haystack import Document
from pydantic import BaseModel
from weaviate.util import generate_uuid5

from ai import ai_chat_thread, update_oncalls
from pipeline import MaxPipeline, split_markdown_sections
from slack import app as slack_app

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


@app.post("/update")
def update_oncall():
    return update_oncalls()


@app.post("/chat")
async def chat(messages: List[Message]):
    print(messages)
    msgs = [msg.dict() for msg in messages]
    response = await ai_chat_thread(msgs)
    return response

@app.get("/_health")
def health():
    return {"status": "ok"}


# Slack Bolt App
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

app_handler = AsyncSlackRequestHandler(slack_app)
@app.post("/slack/events")
async def slack_events(req: Request):
    return await app_handler.handle(req)

