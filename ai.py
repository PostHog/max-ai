import os

from dotenv import load_dotenv
import openai

from haystack.document_stores.weaviate import WeaviateDocumentStore
from haystack.pipelines import Pipeline
from haystack.nodes import Shaper
from haystack.nodes import EmbeddingRetriever

OPENAI_MODEL = "gpt-3.5-turbo"
load_dotenv()

## Initialize OpenAI
openai.api_key = os.environ.get("OPENAI_TOKEN")

## "gpt-4" and "gpt-3.5-turbo" are the two we'll use here

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

def ai_chat_thread(thread):
    pipeline = Pipeline()

    shaper = Shaper(func="join_documents", inputs={"documents": "documents"}, outputs=["documents"])

    pipeline.add_node(retriever, name="Retriever", inputs=["Query"])
    pipeline.add_node(shaper, name="Shaper", inputs=["Retriever"])

    result = pipeline.run(query=thread[0]["content"], params={"Retriever": {"top_k": 10}}, debug=True)

    documents = result["documents"][0].content.replace('\n', '')

    SYSTEM_PROMPT = f"""
    You are the trusty PostHog support bot on Slack named Max.
    Please continue the conversation in a way that is helpful to the user and also makes the user feel like they are talking to a human.
    Only suggest using PostHog products and services. Do not suggest products or services from other companies.
    All relative links should point to domain posthog.com.
    Please answer the question according to the following context from the PostHog documentation.
    ===
    Context:
    {documents}
    """

    print("SYSTEM PROMPT:" + SYSTEM_PROMPT)

    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL, messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *thread,
        ]
    )

    return completion.choices[0].message.content


def summarize_thread(thread):
    prompt = f"""The following is a conversation in which the first person asks a question. Eventually, after the second person may ask some clairfying questions to gain more context, a solution may be reached.
    There may be multiple questions and solutions in the conversation, but only quesitons from the initial person should be considered relevant - questions from other people are just for
    clarifications about the first user's problem. Summarize each question and its solution succintly, excluding distinct user information but mostly just parsing out the relevant content,
    the question that was asked in detail including important context, and the eventual solution. If no solution seems to have been reached, say 'contact PostHog support'.
    Respond in the format of:
    Question: <question>
    Solution: <solution>
    Here is the conversation: {thread}"""
    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content
