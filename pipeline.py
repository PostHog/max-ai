import os
import re
from typing import List

import qdrant_client
from dotenv import load_dotenv
from git import Repo
from langchain.docstore.document import Document
from langchain.document_loaders import GitLoader
from langchain.text_splitter import MarkdownTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from pydantic import BaseModel


load_dotenv()

EXAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "example_data")


class Entry(BaseModel):
    content: str
    meta: dict


class Entries(BaseModel):
    entries: List[Entry]


class MaxPipeline:
    def __init__(self, openai_token: str):
        self.openai_token = openai_token
        self.embeddings = OpenAIEmbeddings()
        self.splitter = MarkdownTextSplitter()

        client = qdrant_client.QdrantClient(path="/tmp/local_qdrant", prefer_grpc=True)
        self.document_store = Qdrant(
            client=client, collection_name="posthog_docs", embeddings=self.embeddings
        )

    def embed_markdown_document(self, documents: Entries):
        for entry in documents.entries:
            texts = self.splitter.split_text(entry.content)

            documents = [
                Document(page_content=doc, metadata=entry.meta) for doc in texts if doc
            ]
            self.embed_documents(documents)

    def embed_documents(self, documents: List[Document]):
        self.document_store.add_documents(documents, index="posthog_docs")

    def retrieve_context(self, query: str):
        result = self.document_store.max_marginal_relevance_search(
            query, k=2, fetch_k=10, index="posthog_docs"
        )

        return result

    def retrieve_git_repo_context(self):
        repo = Repo.clone_from(
            "https://github.com/posthog/posthog.com",
            to_path=EXAMPLE_DATA_DIR,
        )
        branch = repo.head.reference
        loader = GitLoader(
            repo_path="./example_data/test_repo1/",
            branch=branch,
            file_filter=lambda file_path: file_path.endswith(".md"),
        )
        data = loader.load()
        for doc in data:
            print(doc)

