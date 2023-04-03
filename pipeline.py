from typing import List
from haystack import Document
from haystack.document_stores.weaviate import WeaviateDocumentStore
from haystack.pipelines import Pipeline
from haystack.nodes import Shaper
import re
from haystack.nodes import EmbeddingRetriever

class MaxPipeline:
    def __init__(self, openai_token: str):
        self.openai_token = openai_token

        self.document_store = WeaviateDocumentStore(
            embedding_dim=1024,
            custom_schema={
              "classes": [
                # {
                #   "class": "Document",
                #   "description": "A class called document",
                #   "vectorizer": "text2vec-openai",
                #   "moduleConfig": {
                #     "text2vec-openai": {
                #       "model": "ada",
                #       "modelVersion": "002",
                #       "type": "text"
                #     }
                #   },
                #   "properties": [
                #     {
                #       "dataType": [
                #         "text"
                #       ],
                #       "description": "Content that will be vectorized",
                #       "moduleConfig": {
                #         "text2vec-openai": {
                #           "skip": False,
                #           "vectorizePropertyName": False
                #         }
                #       },
                #       "name": "content"
                #     }
                #   ]
                # },
                {
                  "class": "ContextDocument",
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
                      "moduleConfig": {
                        "text2vec-openai": {
                          "skip": False,
                          "vectorizePropertyName": False
                        }
                      },
                      "name": "content"
                    }
                  ]
                },

              ]
            },
            additional_headers={"X-OpenAI-Api-Key": self.openai_token},
        )

        self.retriever = EmbeddingRetriever(
            document_store=self.document_store,
            batch_size=16,
            embedding_model="ada",
            api_key=self.openai_token,
            max_seq_len=768,
        )

    def embed_documents(self, documents: List[Document]):
        self.document_store.write_documents(documents, index="ContextDocument")

    def update_embeddings(self):
        self.document_store.update_embeddings(self.retriever, index="ContextDocument")

        # TODO: only update embeddings for docs we just inserted
        # self.document_store.update_embeddings(self.retriever, index="ContextDocument", filters={
        #     "id": {"$in": [doc.id for doc in documents]}
        # })

    def retrieve_context(self, query: str):
        pipeline = Pipeline()

        # TODO: Try using pipelines to retrieve the answer as well instead of the OpenAi SDK
        # prompt_model = PromptModel("gpt-3.5-turbo", api_key=os.getenv("OPENAI_TOKEN"))
        # prompt_template = PromptTemplate("PROMPT {query}")
        # prompt_node = PromptNode(prompt_model, template)

        shaper = Shaper(func="join_documents", inputs={"documents": "documents"}, outputs=["documents"])

        pipeline.add_node(self.retriever, name="Retriever", inputs=["Query"])
        pipeline.add_node(shaper, name="Shaper", inputs=["Retriever"])

        result = pipeline.run(query=query, params={"Retriever": {"top_k": 10, "index": "ContextDocument"}}, debug=True)

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

