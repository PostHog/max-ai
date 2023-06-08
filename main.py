import logging
import os
from typing import List

import sentry_sdk
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ai import ai_chat_thread
from pipeline import MaxPipeline, Entries
from slack import app as slack_app

load_dotenv()  # take environment variables from .env.

sentry_sdk.init(
    dsn="https://4a3780ef52824c52b13eeab44ea73a14@o1015702.ingest.sentry.io/4505009495605248",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production,
    traces_sample_rate=1.0,
)

origins = [
    "http://localhost",
    "http://localhost:8000",
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


class Message(BaseModel):
    role: str
    content: str

class Query(BaseModel):
    query: str


pipeline = MaxPipeline(openai_token=os.getenv("OPENAI_TOKEN"))


@app.post("/entries")
def create_entries(entries: Entries):
    pipeline.embed_markdown_document(entries)
    return []


@app.post("/_git")
def create_git_entries():
    print("git")
    pipeline.embed_git_repo()
    return {"status": "ok"}


@app.post("/_chat")
def test_chat(query: Query):
    return pipeline.chat(query.query)


@app.post("/_context")
def test_context(query: Query):
    return pipeline.retrieve_context(query.query)


@app.post("/spawn")
def receive_spawn():
    print("Spawned")
    return []


@app.post("/update")
def update_oncall():
    return "nope" 


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


@app.get("/slack/oauth_redirect")
async def oauth_redirect(req: Request):
    logging.info("Installation completed.")
    return await app_handler.handle(req)


@app.get("/slack/install")
async def install(req: Request):
    return await app_handler.handle(req)
