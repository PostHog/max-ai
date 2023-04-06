import os

import openai
from dotenv import load_dotenv

from inference import OpenAIModel

load_dotenv()  # take environment variables from .env.

openai.api_key = os.environ.get("OPENAI_TOKEN")

prompt = """

You are a bot that returns a single word: "FEATURE FLAGS", "EXPERIMENTS", or "OTHERS". Given a question, you must return whether the question
falls into the category of feature flags, experiments, or others.

For example, the question below falls into the category of "FEATURE FLAGS":

Feature Flagged Called By Unique Users is Greater Than Daily Active Users
Hi. Im running an experiment and noticed that on any given the day, the sum of “feature flagged called by unique users” is greater than Daily Active users. How can this be possbile?
Attached screenshots for reference: Daily active is 3,127, but feature flag called is around 4,000?
2. My experiment is rolled out to 20% of users. In the “feature flaged called” chart, I see 4 groups. Test, control (these are expected) and then also “false” and “none”. What is the difference between “false” and “none”? Shouldn’t they be in the same group?


For example, the question below falls into the category of "OTHERS":

How to create a cohort of users who performed a specific event?

How do I filter out internal and test users?

What is the weather like?

Hi friends I'm feeling great today, do you want to try my new app?

How do I capture fewer session recordings?

How do I create an insight?

How do I update a helm chart?

What are the types graphs support?

---

Now classify the question below. Remember to return only one word.

"""



async def classify_question(question, model=OpenAIModel.GPT_3_TURBO.value):
  messages = [
    {"role": "system", "content": "You are a helpful assistant that answers user queries."},
    {"role": "user", "content": prompt + question},
  ]

  api_response = await openai.ChatCompletion.create(
    model=model,
    messages=messages
  )

  classification = api_response["choices"][0]["message"]["content"]

  return "FEATURE FLAGS" in classification or "EXPERIMENTS" in classification


# print(classify_question("How do I get whether a flag is enabled or not?"))