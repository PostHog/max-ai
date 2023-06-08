import os
import re
from typing import List
from pprint import pprint

import weaviate
from dotenv import load_dotenv
from git import Repo
from langchain.docstore.document import Document
from langchain.document_loaders import GitLoader
from langchain.text_splitter import MarkdownTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain import OpenAI
from langchain.vectorstores import Weaviate
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
        embed_setting = os.getenv("EMBEDDING_METHOD", "openai")
        if embed_setting == "openai":
            print("Using OpenAI embeddings")
            self.embeddings = OpenAIEmbeddings()
        elif embed_setting == "huggingface":
            print("Using HuggingFace embeddings")
            self.embeddings = HuggingFaceEmbeddings(model_name="all-mpnet-base-v2")
        self.splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=0)

        weaviate_auth_config = weaviate.AuthApiKey(
            api_key=os.getenv("WEAVIATE_API_KEY")
        )

        weaviate_client = weaviate.Client(
            url=os.getenv("WEAVIATE_URL"), auth_client_secret=weaviate_auth_config
        )

        self.document_store = Weaviate(
            client=weaviate_client,
            index_name="Posthog_docs",
            by_text=False,
            text_key="page_content",
            embedding=self.embeddings,
            attributes=["source"],
        )

        self.retriever = self.document_store.as_retriever(search_type="mmr")

    def embed_markdown_document(self, documents: Entries):
        for entry in documents.entries:
            texts = self.splitter.split_text(entry.content)

            documents = [
                Document(page_content=doc, metadata=entry.meta) for doc in texts if doc
            ]
            self.embed_documents(documents)

    def embed_documents(self, documents: List[Document]):
        self.document_store.add_documents(documents)

    def retrieve_context(self, query: str):
        result = self.retriever.get_relevant_documents(query)
        return result

    def chat(self, query: str):
        chain = RetrievalQAWithSourcesChain.from_chain_type(
            OpenAI(temperature=0), chain_type="stuff", retriever=self.retriever
        )
        results = chain(
            {"question": query},
            return_only_outputs=True,
        )
        return results

    def embed_git_repo(self):
        if not os.path.exists(EXAMPLE_DATA_DIR):
            print("Repo not found, cloning...")
            repo = Repo.clone_from(
                "https://github.com/posthog/posthog.com",
                to_path=EXAMPLE_DATA_DIR,
            )
        else:
            print("Repo already exists, pulling latest changes...")
            repo = Repo(EXAMPLE_DATA_DIR)
            repo.git.pull()

        branch = repo.head.reference
        loader = GitLoader(
            repo_path=EXAMPLE_DATA_DIR,
            branch=branch,
            file_filter=lambda file_path: file_path.endswith(".md"),
        )
        data = loader.load()
        for page in data:
            docs = []
            text = self.splitter.split_text(page.page_content)
            metadata = page.metadata
            print(f"Adding {page.metadata['source']}")
            for token in text:
                docs.append(Document(page_content=token, metadata=metadata))
            self.document_store.add_documents(docs)
