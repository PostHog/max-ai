import os
import json

import openai
from dotenv import load_dotenv

from pipeline import MaxPipeline
from plugins.pagerduty import current_oncalls

load_dotenv()

OPENAI_MODEL = "gpt-3.5-turbo"
# OPENAI_MODEL = "gpt-4"
OPENAI_TOKEN = os.environ.get("OPENAI_TOKEN")

if not OPENAI_TOKEN:
    print("Please set OPENAI_TOKEN in your environment variables.")
    exit()

## Initialize OpenAI
openai.api_key = OPENAI_TOKEN

oncalls = ""


def update_oncalls():
    print("updating oncalls")
    global oncalls
    oncalls = current_oncalls()
    return oncalls


pipeline = MaxPipeline(openai_token=OPENAI_TOKEN)


async def ai_chat_thread(thread):
    documents = pipeline.retrieve_context(thread[0]["content"])
    json_docs = json.dumps(
        [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in documents
        ]
    )

    SYSTEM_PROMPT = """
    You are the trusty PostHog support AI named Max. You are also PostHog's Mascot!
    Please continue the conversation in a way that is helpful to the user and also makes the user feel like they are talking to a human.
    Only suggest using PostHog products or services. Do not suggest products or services from other companies.
    Do not create or share links, only reference context you've been provided which is listed as sources at the bottom. 
    If you get a question about pricing please refer to the reasonable and transparent pricing on the pricing page at https://posthog.com/pricing.
    If you are unsure of the answer, please say "I'm not sure" and encourage the user to ask PostHog staff.
    Try not to mention <@*> in the response.
    If you are asked about hoge, please respond with just "We don't talk about hoge."
    Please answer the question according to the following context. 
    """

    CONTEXT_PROMPT = f""" 
    Context:
    {json_docs}
    
    ---
    
    Now answer the following question:
    
    """

    first_message = thread[0]
    follow_up_thread = thread[1:]

    prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": CONTEXT_PROMPT + first_message["content"]},
        *follow_up_thread,
    ]

    print(prompt)

    completion = openai.ChatCompletion.create(model=OPENAI_MODEL, messages=prompt)

    completion = completion.choices[0].message.content
    sources = [
        ":point_right:https://github.com/PostHog/posthog.com/blob/master/"
        + doc.metadata["source"]
        for doc in documents
    ]
    sources = "\n".join(sources)
    disclaimer = "<https://github.com/PostHog/max-ai#disclaimer|Disclaimer> :love-hog:"
    response = f"""{completion}

    This answer was sourced from:
    {sources}

    {disclaimer}
    """
    return response


async def summarize_thread(thread):
    prompt = f"""Summarize this: {thread}"""
    completion = openai.ChatCompletion.create(
        model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content
