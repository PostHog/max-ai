import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from haystack import Document
from haystack.document_stores.weaviate import WeaviateDocumentStore
from haystack.pipelines import GenerativeQAPipeline
import re
from haystack.nodes import EmbeddingRetriever
from haystack.nodes import OpenAIAnswerGenerator

load_dotenv()  # take environment variables from .env.


app = FastAPI()

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
    max_seq_len=1024,
)


generator = OpenAIAnswerGenerator(api_key=os.getenv("OPENAI_TOKEN"), max_tokens=1024)

class Entry(BaseModel):
    id: str
    slug: str
    rawBody: str

class Entries(BaseModel):
    entries: List[Entry]

@app.post("/entries")
def create_entries(entries: Entries):
    for entry in entries.entries:
        headings = split_markdown_sections(entry.rawBody)

        documents = [Document(content=doc) for doc in headings]
        document_store.write_documents(documents, index="Document")

    document_store.update_embeddings(retriever)

    return []

@app.get("/search")
def search_entries(query: str):
    pipeline = GenerativeQAPipeline(generator=generator, retriever=retriever)

    result = pipeline.run(query, params={"Retriever": {"top_k": 10}})

    if result is None:
        return []

    return result["answers"]

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
