import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from haystack import Document
from haystack.document_stores.weaviate import WeaviateDocumentStore
from haystack.pipelines import Pipeline, GenerativeQAPipeline
from haystack.nodes import PromptTemplate, PromptModel, PromptNode, Shaper
import re
from haystack.nodes import EmbeddingRetriever
from haystack.nodes import OpenAIAnswerGenerator

from ai import ai_chat_thread


load_dotenv()  # take environment variables from .env.

app = FastAPI()
origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_store = WeaviateDocumentStore(
    embedding_dim=1024,
    custom_schema={
      "classes": [
        {
          "class": "Document",
          "description": "A class called document",
          "vectorizer": "text2vec-openai",
          "moduleConfig": {
            "text2vec-openai": {
              "model": "ada",
              "modelVersion": "002",
              "type": "text"
            }
          },
          "properties": [
            {
              "dataType": [
                "text"
              ],
              "description": "Content that will be vectorized",
              "moduleConfig": {
                "text2vec-openai": {
                  "skip": False,
                  "vectorizePropertyName": False
                }
              },
              "name": "content"
            }
          ]
        }
      ]
    },
    additional_headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_TOKEN")},
)

retriever = EmbeddingRetriever(
    document_store=document_store,
    batch_size=16,
    embedding_model="ada",
    api_key=os.getenv("OPENAI_TOKEN"),
    max_seq_len=2048,
)

class Entry(BaseModel):
    id: str
    slug: str
    rawBody: str

class Entries(BaseModel):
    entries: List[Entry]

class Message(BaseModel):
    role: str
    content: str

@app.post("/entries")
def create_entries(entries: Entries):
    for entry in entries.entries:
        headings = split_markdown_sections(entry.rawBody)

        documents = [Document(content=doc) for doc in headings]
        document_store.write_documents(documents, index="Document")

    document_store.update_embeddings(retriever)

    return []

@app.post("/chat")
def chat(messages: List[Message]):
    msgs = [msg.dict() for msg in messages]
    print(msgs) 
    response = ai_chat_thread(msgs)
    return response

@app.post("/search")
def search_entries(query: str, messages: List[Message):
    pipeline = Pipeline()

    prompt_template = PromptTemplate(
       name="question-answering-with-examples",
       prompt_text="""
           You are the trusty PostHog support bot on Slack named Max.
           Please continue the conversation in a way that is helpful to the user and also makes the user feel like they are talking to a human.
           Only suggest using PostHog products and services. Do not suggest products or services from other companies.
           Please answer the question according to the following context from the PostHog documentation.
           ===
           Context:
           {documents}
           ===
           {query}""",
    )

    prompt_model = PromptModel("gpt-3.5-turbo", api_key=os.getenv("OPENAI_TOKEN"))
    prompt_node = PromptNode(prompt_model, output_variable="answer", default_prompt_template=prompt_template)

    shaper = Shaper(func="join_documents", inputs={"documents": "documents"}, outputs=["documents"])

    pipeline.add_node(retriever, name="Retriever", inputs=["Query"])
    pipeline.add_node(shaper, name="Shaper", inputs=["Retriever"])
    # pipeline.add_node(component=prompt_node, name="PromptNode", inputs=["Shaper"])
    result = pipeline.run(query=query, params={"Retriever": {"top_k": 10}}, debug=True)

    


    if result is None:
        return []

    return result

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

