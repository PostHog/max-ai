import os

from dotenv import load_dotenv
import openai

load_dotenv()

## Initialize OpenAI
openai.api_key = os.environ.get("OPENAI_TOKEN")
models = [m.id for m in openai.Model.list()["data"]]
print(f"Available models: {', '.join(models)}")

## "gpt-4" and "gpt-3.5-turbo" are the two we'll use here


def ai_chat_thread(thread):
    SYSTEM_PROMPT = """
    You are the trusty PostHog support bot on Slack named Max.
    Please continue the conversation in a way that is helpful to the user and also makes the user feel like they are talking to a human.
    Only suggest using PostHog products and services. Do not suggest products or services from other companies.
    """
    prompt = f"{thread}"
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *thread,
                {"role": "user", "content": prompt}
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
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content