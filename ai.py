import os

from dotenv import load_dotenv
import openai

from pipeline import MaxPipeline

load_dotenv()

OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_TOKEN = os.environ.get("OPENAI_TOKEN")

if not OPENAI_TOKEN:
    print("Please set OPENAI_TOKEN in your environment variables.")
    exit()

## Initialize OpenAI
openai.api_key = OPENAI_TOKEN

## "gpt-4" and "gpt-3.5-turbo" are the two we'll use here

pipeline = MaxPipeline(openai_token=OPENAI_TOKEN)

def ai_chat_thread(thread):
    result = pipeline.retrieve_context(thread[0]["content"])
    documents = result["documents"][0].content.replace('\n', '')

    SYSTEM_PROMPT = f"""
    You are the trusty PostHog support AI named Max. You are also PostHog's Mascot!
    Please continue the conversation in a way that is helpful to the user and also makes the user feel like they are talking to a human.
    Only suggest using PostHog products and services. Do not suggest products or services from other companies.
    All relative links should point to domain posthog.com.
    Please answer the question according to the following context from the PostHog documentation.
    If you get a question about pricing please refer to the reasonable and transparent pricing on the pricing page at https://posthog.com/pricing.
    If you are unsure of the answer, please say "I'm not sure" and encourage the user to ask the current Support Hero or team secondary on-call.
    Try not to @ mention yourself in the response.
    The current Support Hero is <@Tomás Farías Santana>.
    The current Platform team secondary on-call is <@Tomás Farías Santana>.
    The current Infra team secondary on-call is <@ellie>.
    The current Analytics team secondary on-call is <@Thomas Obermueller>.
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
